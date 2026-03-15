from pathlib import Path, PurePosixPath
from urllib.parse import quote

from fastapi import HTTPException, Request


def project_dir_or_404(project_id: str, request: Request) -> Path:
    project_dir = Path(request.app.state.workspace_root) / project_id
    if not (project_dir / "project.json").exists():
        raise HTTPException(status_code=404, detail="Project not found")
    return project_dir


def project_media_url(project_id: str, relative_path: str | None) -> str | None:
    if relative_path is None:
        return None

    normalized_path = _normalize_relative_path(relative_path)
    return f"/projects/{project_id}/media/{quote(normalized_path, safe='/')}"


def resolve_project_media_file(project_dir: Path, media_path: str) -> Path:
    normalized_path = _normalize_relative_path(media_path)
    candidate = (project_dir / Path(*PurePosixPath(normalized_path).parts)).resolve()
    project_root = project_dir.resolve()

    try:
        candidate.relative_to(project_root)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=f"Project media not found: {normalized_path}") from error

    if not candidate.is_file():
        raise HTTPException(status_code=404, detail=f"Project media not found: {normalized_path}")

    return candidate


def _normalize_relative_path(raw_path: str) -> str:
    normalized_path = PurePosixPath(raw_path.replace("\\", "/").lstrip("/"))
    if (
        str(normalized_path) in {"", "."}
        or normalized_path.is_absolute()
        or any(part in {"..", ""} for part in normalized_path.parts)
    ):
        raise HTTPException(status_code=404, detail=f"Project media not found: {raw_path}")

    return normalized_path.as_posix()
