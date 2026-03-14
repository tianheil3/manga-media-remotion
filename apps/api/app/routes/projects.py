import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request

from apps.api.app.services.file_store import FileStore

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("")
def list_projects(request: Request) -> list[dict[str, object]]:
    workspace_root = _workspace_root(request)
    projects: list[dict[str, object]] = []
    for project_dir in sorted(workspace_root.iterdir(), key=lambda path: path.name):
        if not project_dir.is_dir() or not (project_dir / "project.json").exists():
            continue

        project = FileStore(project_dir).load_project()
        projects.append(
            {
                "id": project.id,
                "title": project.title,
                "progress": _project_progress(project_dir),
            }
        )

    return projects


@router.get("/{project_id}")
def get_project(project_id: str, request: Request) -> dict[str, object]:
    project_dir = _workspace_root(request) / project_id
    if not (project_dir / "project.json").exists():
        raise HTTPException(status_code=404, detail="Project not found")

    store = FileStore(project_dir)
    project = store.load_project()
    frames = store.load_frames()
    voices = _load_optional_list(store.load_voices)
    scenes = _load_optional_list(store.load_scenes)

    return {
        "id": project.id,
        "title": project.title,
        "progress": _project_progress(project_dir),
        "counts": {
            "frames": len(frames),
            "voices": len(voices),
            "scenes": len(scenes),
        },
    }


def _workspace_root(request: Request) -> Path:
    return Path(request.app.state.workspace_root)


def _project_progress(project_dir: Path) -> dict[str, bool]:
    store = FileStore(project_dir)
    frames = _load_optional_list(store.load_frames)
    voices = _load_optional_list(store.load_voices)
    scenes = _load_optional_list(store.load_scenes)

    translation_ready = False
    script_path = project_dir / "script" / "script.json"
    if script_path.exists():
        translation_ready = len(json.loads(script_path.read_text(encoding="utf-8"))) > 0

    return {
        "images": len(frames) > 0,
        "ocr": any(frame.bubbles for frame in frames),
        "review": any(frame.reviewed_bubbles for frame in frames),
        "translation": translation_ready,
        "voice": any(voice.audio_file for voice in voices),
        "scenes": len(scenes) > 0,
    }


def _load_optional_list(loader):
    try:
        return loader()
    except FileNotFoundError:
        return []
