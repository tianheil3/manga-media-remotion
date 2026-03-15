import json
from pathlib import Path
import sys
from types import SimpleNamespace

from fastapi import BackgroundTasks, HTTPException
import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.api.app.models.project import Project
from apps.api.app.models.scene import Scene
from apps.api.app.routes.render import RenderRequest, create_render_job, get_render_job
from apps.api.app.services.file_store import FileStore
from apps.api.app.services.render_jobs import create_job


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


def create_scenes(workspace_root: Path, project_id: str) -> None:
    project_dir = workspace_root / project_id
    store = FileStore(project_dir)
    store.save_scenes(
        [
            Scene(
                id="scene-001",
                type="narration",
                image="images/001.png",
                subtitleText="Opening line",
                durationMs=1000,
                stylePreset="default",
            )
        ]
    )


def run_background_tasks(background_tasks: BackgroundTasks) -> None:
    for task in background_tasks.tasks:
        task.func(*task.args, **task.kwargs)


def test_create_render_job_persists_a_queued_job(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    create_project(workspace_root, "demo-001")
    request = make_request(workspace_root)
    background_tasks = BackgroundTasks()

    job = create_render_job("demo-001", RenderRequest(kind="preview"), request, background_tasks)

    assert job["id"] == "render-preview-001"
    assert job["projectId"] == "demo-001"
    assert job["kind"] == "preview"
    assert job["status"] == "queued"
    assert job["outputFile"] == "/projects/demo-001/media/renders/preview-render-preview-001.mp4"
    assert job["statusPath"] == "/projects/demo-001/render-jobs/render-preview-001"
    assert job["createdAt"].endswith("Z")
    assert job["updatedAt"].endswith("Z")


def test_get_render_job_is_idempotent_and_does_not_mutate_state(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    create_project(workspace_root, "demo-001")
    request = make_request(workspace_root)
    project_dir = workspace_root / "demo-001"

    created_job = create_job(project_dir, kind="final")
    first = get_render_job("demo-001", created_job.id, request)
    second = get_render_job("demo-001", created_job.id, request)

    assert first["status"] == "queued"
    assert second["status"] == "queued"
    assert first["updatedAt"] == created_job.updated_at
    assert second["updatedAt"] == created_job.updated_at


def test_get_render_job_returns_actionable_404_for_unknown_jobs(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    create_project(workspace_root, "demo-001")
    request = make_request(workspace_root)

    with pytest.raises(HTTPException) as error:
        get_render_job("demo-001", "render-preview-999", request)

    assert error.value.status_code == 404
    assert error.value.detail == "Unknown render job: render-preview-999"


def test_post_render_job_starts_real_renders_and_persists_non_empty_output_files(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / "workspace"
    create_project(workspace_root, "demo-001")
    create_scenes(workspace_root, "demo-001")
    request = make_request(workspace_root)

    for kind in ("preview", "final"):
        background_tasks = BackgroundTasks()
        created_job = create_render_job(
            "demo-001",
            RenderRequest(kind=kind),
            request,
            background_tasks,
        )
        run_background_tasks(background_tasks)
        completed_job = get_render_job("demo-001", created_job["id"], request)
        output_file = completed_job["outputFile"].removeprefix("/projects/demo-001/media/")
        output_path = workspace_root / "demo-001" / output_file

        assert created_job["status"] == "queued"
        assert completed_job["status"] == "completed"
        assert completed_job.get("errorMessage") is None
        assert completed_job["updatedAt"] != created_job["updatedAt"]
        assert output_path.exists()
        assert output_path.stat().st_size > 0

        artifact = json.loads(output_path.read_text(encoding="utf-8"))
        assert artifact["artifactType"] == "manga-remotion-render-v1"
        assert artifact["kind"] == kind
        assert artifact["project"]["id"] == "demo-001"
        assert artifact["sceneCount"] == 1


def test_failed_render_jobs_persist_error_messages(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    create_project(workspace_root, "demo-001")
    request = make_request(workspace_root)
    background_tasks = BackgroundTasks()

    created_job = create_render_job(
        "demo-001",
        RenderRequest(kind="preview"),
        request,
        background_tasks,
    )
    run_background_tasks(background_tasks)
    failed_job = get_render_job("demo-001", created_job["id"], request)

    assert failed_job["status"] == "failed"
    assert "scenes" in (failed_job.get("errorMessage") or "").lower()
