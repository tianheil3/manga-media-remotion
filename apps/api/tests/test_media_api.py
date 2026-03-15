from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

from fastapi import HTTPException

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.api.app.models.project import Project
from apps.api.app.routes.media import get_project_media
from apps.api.app.services.file_store import FileStore


def create_project(workspace_root: Path, project_id: str) -> Path:
    project_dir = workspace_root / project_id
    store = FileStore(project_dir)
    store.save_project(
        Project(
            id=project_id,
            title=f"Project {project_id}",
            sourceLanguage="ja",
            imageDir="images",
            createdAt="2026-03-14T00:00:00Z",
            updatedAt="2026-03-14T00:00:00Z",
        )
    )
    return project_dir


def test_media_route_serves_project_files_and_returns_actionable_404s(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    project_dir = create_project(workspace_root, "demo-001")
    media_path = project_dir / "images" / "001.png"
    media_path.parent.mkdir(parents=True, exist_ok=True)
    media_path.write_bytes(b"png-bytes")
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(workspace_root=workspace_root)))

    response = get_project_media("demo-001", "images/001.png", request)

    assert response.status_code == 200
    assert Path(response.path) == media_path

    with pytest.raises(HTTPException) as error:
        get_project_media("demo-001", "renders/missing.mp4", request)

    assert error.value.status_code == 404
    assert error.value.detail == "Project media not found: renders/missing.mp4"
