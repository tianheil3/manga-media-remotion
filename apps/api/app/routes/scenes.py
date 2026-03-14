from pathlib import Path

from fastapi import APIRouter, HTTPException, Request

from apps.api.app.services.file_store import FileStore

router = APIRouter(prefix="/projects", tags=["scenes"])


@router.get("/{project_id}/scenes")
def get_scenes(project_id: str, request: Request) -> list[dict[str, object]]:
    project_dir = Path(request.app.state.workspace_root) / project_id
    if not (project_dir / "project.json").exists():
        raise HTTPException(status_code=404, detail="Project not found")

    store = FileStore(project_dir)
    try:
        scenes = store.load_scenes()
    except FileNotFoundError:
        return []

    return [scene.model_dump(mode="json", by_alias=True) for scene in scenes]
