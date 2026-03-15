from fastapi import APIRouter, Request

from apps.api.app.models.scene import Scene
from apps.api.app.services.file_store import FileStore
from apps.api.app.services.project_media import project_dir_or_404, project_media_url

router = APIRouter(prefix="/projects", tags=["scenes"])


@router.get("/{project_id}/scenes")
def get_scenes(project_id: str, request: Request) -> list[dict[str, object]]:
    project_dir = project_dir_or_404(project_id, request)
    store = FileStore(project_dir)
    try:
        scenes = store.load_scenes()
    except FileNotFoundError:
        return []

    return [_scene_payload(project_id, scene) for scene in scenes]


def _scene_payload(project_id: str, scene: Scene) -> dict[str, object]:
    payload = scene.model_dump(mode="json", by_alias=True)
    payload["image"] = project_media_url(project_id, scene.image)
    payload["audio"] = project_media_url(project_id, scene.audio)
    return payload
