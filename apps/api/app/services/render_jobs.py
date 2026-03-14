import json
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
    )
    jobs.append(job)
    _save_jobs(project_dir, jobs)
    return job


def get_job(project_dir: Path, job_id: str) -> RenderJob:
    jobs = load_jobs(project_dir)
    for index, job in enumerate(jobs):
        if job.id != job_id:
            continue

        next_job = _advance_job(project_dir, job)
        if next_job is not None:
            jobs[index] = next_job
            _save_jobs(project_dir, jobs)
        return job
    raise ValueError(f"Unknown render job: {job_id}")


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


def _advance_job(project_dir: Path, job: RenderJob) -> RenderJob | None:
    # Advance on read so the file-backed MVP can expose progress without a worker.
    if job.status == "queued":
        return job.model_copy(update={"status": "running", "updated_at": _utc_timestamp()})

    if job.status == "running":
        output_path = Path(project_dir) / job.output_file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"")
        return job.model_copy(update={"status": "completed", "updated_at": _utc_timestamp()})

    return None


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
