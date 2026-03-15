from __future__ import annotations

import shutil
from pathlib import Path
import sys
from types import SimpleNamespace

from fastapi import BackgroundTasks
from typer.testing import CliRunner

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.api.app.routes.media import get_project_media
from apps.api.app.routes.projects import get_project, list_projects
from apps.api.app.routes.render import RenderRequest, create_render_job, get_render_job
from apps.api.app.routes.review import get_frames
from apps.api.app.routes.scenes import get_scenes
from apps.cli.app.main import app

PROJECT_ID = "demo-001"
FIXTURE_PROJECT_DIR = ROOT / "tests" / "fixtures" / "workspace" / PROJECT_ID

runner = CliRunner()


def make_request(workspace_root: Path) -> SimpleNamespace:
    return SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(workspace_root=workspace_root)))


def run_background_tasks(background_tasks: BackgroundTasks) -> None:
    for task in background_tasks.tasks:
        task.func(*task.args, **task.kwargs)


def copy_fixture_project(tmp_path: Path) -> Path:
    assert FIXTURE_PROJECT_DIR.exists(), f"Missing sample project fixture: {FIXTURE_PROJECT_DIR}"

    workspace_root = tmp_path / "workspace"
    shutil.copytree(FIXTURE_PROJECT_DIR, workspace_root / PROJECT_ID)
    return workspace_root


def test_sample_project_fixture_has_workspace_shape() -> None:
    assert FIXTURE_PROJECT_DIR.exists()
    assert (FIXTURE_PROJECT_DIR / "project.json").exists()
    assert (FIXTURE_PROJECT_DIR / "config.json").exists()
    assert (FIXTURE_PROJECT_DIR / "images" / "001.png").exists()
    assert (FIXTURE_PROJECT_DIR / "ocr" / "001.json").exists()
    assert (FIXTURE_PROJECT_DIR / "script" / "frames.json").exists()
    assert (FIXTURE_PROJECT_DIR / "script" / "script.json").exists()
    assert (FIXTURE_PROJECT_DIR / "script" / "voices.json").exists()
    assert (FIXTURE_PROJECT_DIR / "script" / "scenes.json").exists()
    assert (FIXTURE_PROJECT_DIR / "audio" / "characters" / "script-bubble-001.wav").exists()


def test_sample_project_smoke_runs_cli_api_and_preview_render(tmp_path: Path) -> None:
    workspace_root = copy_fixture_project(tmp_path)
    request = make_request(workspace_root)

    result = runner.invoke(
        app,
        ["run", PROJECT_ID, "--workspace-root", str(workspace_root)],
    )

    assert result.exit_code == 0, result.stdout
    assert "Project demo-001 progress" in result.stdout
    assert "[done] import-images" in result.stdout
    assert "[done] ocr" in result.stdout
    assert "[done] review" in result.stdout
    assert "[done] translate" in result.stdout
    assert "[done] voice" in result.stdout
    assert "[done] build-scenes" in result.stdout
    assert "Next stage: complete" in result.stdout

    assert list_projects(request) == [
        {
            "id": PROJECT_ID,
            "title": "Sample Project Fixture",
            "progress": {
                "images": True,
                "ocr": True,
                "review": True,
                "translation": True,
                "voice": True,
                "scenes": True,
            },
        }
    ]

    assert get_project(PROJECT_ID, request) == {
        "id": PROJECT_ID,
        "title": "Sample Project Fixture",
        "progress": {
            "images": True,
            "ocr": True,
            "review": True,
            "translation": True,
            "voice": True,
            "scenes": True,
        },
        "counts": {
            "frames": 1,
            "voices": 1,
            "scenes": 1,
        },
    }

    frames = get_frames(PROJECT_ID, request)
    assert len(frames) == 1
    assert frames[0]["frameId"] == "frame-001"
    assert frames[0]["image"] == f"/projects/{PROJECT_ID}/media/images/001.png"
    assert frames[0]["reviewedBubbles"] == [
        {
            "id": "review-bubble-001",
            "sourceBubbleId": "bubble-001",
            "textOriginal": "サンプルです。",
            "textEdited": "サンプルです。",
            "order": 0,
            "kind": "dialogue",
            "speaker": "Hero",
        }
    ]

    scenes = get_scenes(PROJECT_ID, request)
    assert scenes == [
        {
            "id": "scene-001",
            "type": "dialogue",
            "image": f"/projects/{PROJECT_ID}/media/images/001.png",
            "subtitleText": "This is a sample line.",
            "voiceId": "voice-script-bubble-001",
            "audio": f"/projects/{PROJECT_ID}/media/audio/characters/script-bubble-001.wav",
            "durationMs": 900,
            "speaker": "Hero",
            "stylePreset": "default",
            "cameraMotion": "none",
            "transition": "cut",
        }
    ]

    image_response = get_project_media(PROJECT_ID, "images/001.png", request)
    assert image_response.status_code == 200
    assert Path(image_response.path).name == "001.png"

    audio_response = get_project_media(PROJECT_ID, "audio/characters/script-bubble-001.wav", request)
    assert audio_response.status_code == 200
    assert Path(audio_response.path).name == "script-bubble-001.wav"

    background_tasks = BackgroundTasks()
    created_job = create_render_job(
        PROJECT_ID,
        RenderRequest(kind="preview"),
        request,
        background_tasks,
    )
    run_background_tasks(background_tasks)
    completed_job = get_render_job(PROJECT_ID, created_job["id"], request)

    assert created_job["status"] == "queued"
    assert completed_job["status"] == "completed"
    assert completed_job["outputFile"] == (
        f"/projects/{PROJECT_ID}/media/renders/preview-render-preview-001.mp4"
    )

    render_media_path = completed_job["outputFile"].removeprefix(f"/projects/{PROJECT_ID}/media/")
    render_response = get_project_media(PROJECT_ID, render_media_path, request)
    assert render_response.status_code == 200
    assert Path(render_response.path).exists()
    assert Path(render_response.path).read_bytes()[4:8] == b"ftyp"


def test_sample_project_portability_smoke_preserves_cli_progress_and_integrity(tmp_path: Path) -> None:
    source_workspace_root = copy_fixture_project(tmp_path / "source")
    archive_path = tmp_path / "demo-001.tar.gz"
    destination_workspace_root = tmp_path / "destination" / "workspace"

    export_result = runner.invoke(
        app,
        [
            "export-workspace",
            PROJECT_ID,
            str(archive_path),
            "--workspace-root",
            str(source_workspace_root),
        ],
    )

    assert export_result.exit_code == 0, export_result.stdout
    assert archive_path.is_file()

    import_result = runner.invoke(
        app,
        [
            "import-workspace",
            str(archive_path),
            "--workspace-root",
            str(destination_workspace_root),
        ],
    )

    assert import_result.exit_code == 0, import_result.stdout

    run_result = runner.invoke(
        app,
        ["run", PROJECT_ID, "--workspace-root", str(destination_workspace_root)],
    )

    assert run_result.exit_code == 0, run_result.stdout
    assert "[done] import-images" in run_result.stdout
    assert "[done] ocr" in run_result.stdout
    assert "[done] review" in run_result.stdout
    assert "[done] translate" in run_result.stdout
    assert "[done] voice" in run_result.stdout
    assert "[done] build-scenes" in run_result.stdout

    integrity_result = runner.invoke(
        app,
        ["integrity", PROJECT_ID, "--workspace-root", str(destination_workspace_root)],
    )

    assert integrity_result.exit_code == 0, integrity_result.stdout
    assert "Project integrity OK." in integrity_result.stdout
