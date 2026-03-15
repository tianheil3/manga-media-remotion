from fastapi import APIRouter, Request
from fastapi.responses import FileResponse

from apps.api.app.services.project_media import project_dir_or_404, resolve_project_media_file

router = APIRouter(prefix="/projects", tags=["media"])


@router.get("/{project_id}/media/{media_path:path}", name="project_media")
def get_project_media(project_id: str, media_path: str, request: Request) -> FileResponse:
    project_dir = project_dir_or_404(project_id, request)
    media_file = resolve_project_media_file(project_dir, media_path)
    return FileResponse(media_file)
