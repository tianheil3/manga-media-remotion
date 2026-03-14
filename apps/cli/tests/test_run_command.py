from pathlib import Path
import sys

from typer.testing import CliRunner

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.api.app.models.frame import Frame, OcrBubble
from apps.api.app.models.project import Project
from apps.api.app.services.file_store import FileStore
from apps.cli.app.main import app

runner = CliRunner()


def create_partially_completed_project(tmp_path: Path) -> Path:
    workspace_root = tmp_path / "workspace"
    project_dir = workspace_root / "demo-001"
    store = FileStore(project_dir)

    store.save_project(
        Project(
            id="demo-001",
            title="Demo Project",
            sourceLanguage="ja",
            imageDir="images",
            createdAt="2026-03-14T00:00:00Z",
            updatedAt="2026-03-14T00:00:00Z",
        )
    )
    store.save_frames(
        [
            Frame(
                frameId="frame-001",
                image="images/001.png",
                ocrFile="ocr/001.json",
                bubbles=[
                    OcrBubble(
                        id="bubble-001",
                        text="raw",
                        bbox={"x": 1, "y": 1, "w": 10, "h": 10},
                        order=0,
                        confidence=0.9,
                        language="ja",
                    )
                ],
                reviewedBubbles=[],
            )
        ]
    )
    return workspace_root


def test_run_command_shows_file_backed_progress_and_next_stage(tmp_path: Path) -> None:
    workspace_root = create_partially_completed_project(tmp_path)

    result = runner.invoke(
        app,
        ["run", "demo-001", "--workspace-root", str(workspace_root)],
    )

    assert result.exit_code == 0, result.stdout
    assert "Project demo-001 progress" in result.stdout
    assert "[done] import-images" in result.stdout
    assert "[done] ocr" in result.stdout
    assert "[pending] review" in result.stdout
    assert "[pending] translate" in result.stdout
    assert "[pending] voice" in result.stdout
    assert "[pending] build-scenes" in result.stdout
    assert "Next stage: review" in result.stdout
