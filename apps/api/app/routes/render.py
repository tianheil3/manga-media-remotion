from pathlib import Path
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from pydantic import BaseModel

from apps.api.app.services.project_media import project_dir_or_404, project_media_url
from apps.api.app.services.render_jobs import create_job, get_job, run_job

router = APIRouter(prefix="/projects", tags=["render"])


class RenderRequest(BaseModel):
    kind: Literal["preview", "final"]


@router.post("/{project_id}/render-jobs")
def create_render_job(
    project_id: str,
    payload: RenderRequest,
    request: Request,
    background_tasks: BackgroundTasks,
) -> dict[str, object]:
    project_dir = _project_dir(project_id, request)
    job = create_job(project_dir, kind=payload.kind)
    background_tasks.add_task(run_job, project_dir, job.id)
    return _job_payload(project_id, job.model_dump(mode="json", by_alias=True))


@router.get("/{project_id}/render-jobs/{job_id}")
def get_render_job(project_id: str, job_id: str, request: Request) -> dict[str, object]:
    project_dir = _project_dir(project_id, request)
    try:
        job = get_job(project_dir, job_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return _job_payload(project_id, job.model_dump(mode="json", by_alias=True))


def _job_payload(project_id: str, job: dict[str, object]) -> dict[str, object]:
    return {
        **job,
        "outputFile": project_media_url(project_id, str(job["outputFile"])),
        "statusPath": f"/projects/{project_id}/render-jobs/{job['id']}",
    }


def _project_dir(project_id: str, request: Request) -> Path:
    return project_dir_or_404(project_id, request)
