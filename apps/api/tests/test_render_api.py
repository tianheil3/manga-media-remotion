from pathlib import Path
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.api.app.models.project import Project
from apps.api.app.routes.render import RenderRequest, create_render_job, get_render_job
from apps.api.app.services.file_store import FileStore


def create_project(workspace_root: Path, project_id: str) -> None:
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


def make_request(workspace_root: Path) -> SimpleNamespace:
    return SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(workspace_root=workspace_root)))


def test_create_render_job_persists_a_queued_job(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    create_project(workspace_root, "demo-001")
    request = make_request(workspace_root)

    job = create_render_job("demo-001", RenderRequest(kind="preview"), request)

    assert job["id"] == "render-preview-001"
    assert job["projectId"] == "demo-001"
    assert job["kind"] == "preview"
    assert job["status"] == "queued"
    assert job["outputFile"] == "renders/preview-render-preview-001.mp4"
    assert job["statusPath"] == "/projects/demo-001/render-jobs/render-preview-001"
    assert job["createdAt"].endswith("Z")
    assert job["updatedAt"].endswith("Z")


def test_get_render_job_returns_persisted_status(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    create_project(workspace_root, "demo-001")
    request = make_request(workspace_root)

    created_job = create_render_job("demo-001", RenderRequest(kind="final"), request)

    assert get_render_job("demo-001", created_job["id"], request) == created_job


def test_render_job_progresses_to_completed_and_writes_output_file(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    create_project(workspace_root, "demo-001")
    request = make_request(workspace_root)

    created_job = create_render_job("demo-001", RenderRequest(kind="preview"), request)
    queued_job = get_render_job("demo-001", created_job["id"], request)
    running_job = get_render_job("demo-001", created_job["id"], request)
    completed_job = get_render_job("demo-001", created_job["id"], request)

    assert created_job["status"] == "queued"
    assert queued_job["status"] == "queued"
    assert running_job["status"] == "running"
    assert completed_job["status"] == "completed"
    assert completed_job["updatedAt"] != created_job["updatedAt"]
    assert (workspace_root / "demo-001" / completed_job["outputFile"]).exists()
