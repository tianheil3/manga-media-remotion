import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

class RenderJob(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    project_id: str = Field(alias="projectId")
    kind: Literal["preview", "final"]
    status: Literal["queued", "running", "completed", "failed"]
    output_file: str = Field(alias="outputFile")
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")
    error_message: str | None = Field(default=None, alias="errorMessage")


def create_job(project_dir: Path, *, kind: Literal["preview", "final"]) -> RenderJob:
    project_id = Path(project_dir).name
    jobs = load_jobs(project_dir)
    sequence = sum(1 for job in jobs if job.kind == kind) + 1
    job_id = f"render-{kind}-{sequence:03d}"
    timestamp = _utc_timestamp()
    job = RenderJob(
        id=job_id,
        projectId=project_id,
        kind=kind,
        status="queued",
        outputFile=f"renders/{kind}-{job_id}.mp4",
        createdAt=timestamp,
        updatedAt=timestamp,
        errorMessage=None,
    )
    jobs.append(job)
    _save_jobs(project_dir, jobs)
    return job


def get_job(project_dir: Path, job_id: str) -> RenderJob:
    return _find_job(load_jobs(project_dir), job_id)


def run_job(project_dir: Path, job_id: str) -> RenderJob:
    job = get_job(project_dir, job_id)
    if job.status in {"completed", "failed"}:
        return job

    running_job = _update_job(
        project_dir,
        job_id,
        status="running",
        error_message=None,
    )

    try:
        _render_job_output(project_dir, running_job)
    except Exception as error:  # pragma: no cover - guarded by API tests
        return _update_job(
            project_dir,
            job_id,
            status="failed",
            error_message=str(error),
        )

    return _update_job(
        project_dir,
        job_id,
        status="completed",
        error_message=None,
    )


def load_jobs(project_dir: Path) -> list[RenderJob]:
    jobs_path = _jobs_path(project_dir)
    if not jobs_path.exists():
        return []
    payload = json.loads(jobs_path.read_text(encoding="utf-8"))
    return [RenderJob.model_validate(item) for item in payload]


def _save_jobs(project_dir: Path, jobs: list[RenderJob]) -> None:
    jobs_path = _jobs_path(project_dir)
    jobs_path.parent.mkdir(parents=True, exist_ok=True)
    payload = [job.model_dump(mode="json", by_alias=True) for job in jobs]
    jobs_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _jobs_path(project_dir: Path) -> Path:
    return Path(project_dir) / "renders" / "jobs.json"


def _update_job(project_dir: Path, job_id: str, **changes: object) -> RenderJob:
    jobs = load_jobs(project_dir)
    updated_job = None
    updated_jobs = []

    for job in jobs:
        if job.id != job_id:
            updated_jobs.append(job)
            continue

        updated_job = job.model_copy(update={**changes, "updated_at": _utc_timestamp()})
        updated_jobs.append(updated_job)

    if updated_job is None:
        raise ValueError(f"Unknown render job: {job_id}")

    _save_jobs(project_dir, updated_jobs)
    return updated_job


def _find_job(jobs: list[RenderJob], job_id: str) -> RenderJob:
    for job in jobs:
        if job.id == job_id:
            return job

    raise ValueError(f"Unknown render job: {job_id}")


def _render_job_output(project_dir: Path, job: RenderJob) -> None:
    output_path = Path(project_dir) / job.output_file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        _render_command(project_dir, job),
        capture_output=True,
        check=False,
        cwd=_repo_root(),
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(_extract_render_error(result))

    if not output_path.exists():
        raise RuntimeError("Render output is missing.")
    if output_path.stat().st_size == 0:
        raise RuntimeError("Render output is empty.")


def _render_command(project_dir: Path, job: RenderJob) -> list[str]:
    return [
        "npm",
        "run",
        "render",
        "--workspace",
        "apps/remotion",
        "--",
        "--project-dir",
        str(project_dir),
        "--kind",
        job.kind,
        "--output-file",
        job.output_file,
    ]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _extract_render_error(result: subprocess.CompletedProcess[str]) -> str:
    for line in reversed((result.stderr + "\n" + result.stdout).splitlines()):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("npm error"):
            continue
        if stripped.startswith(">"):
            continue
        return stripped.removeprefix("Error: ")

    return "Renderer command failed."


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
