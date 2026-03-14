import json
from pathlib import Path
import sys

from typer.testing import CliRunner

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.api.app.models.frame import Frame, OcrBubble, ReviewedBubble
from apps.api.app.models.project import Project
from apps.api.app.services.file_store import FileStore
from apps.cli.app.main import app
import apps.cli.app.services.translation_service as translation_service

runner = CliRunner()


class FakeTranslationService:
    def translate_text(self, text: str, source_language: str, target_language: str) -> str:
        return f"{target_language}:{text}"


def create_project_with_reviewed_frame(tmp_path: Path) -> tuple[Path, Path]:
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
                        text="raw ocr",
                        bbox={"x": 1, "y": 1, "w": 10, "h": 10},
                        order=0,
                        confidence=0.9,
                        language="ja",
                    )
                ],
                reviewedBubbles=[
                    ReviewedBubble(
                        id="review-bubble-001",
                        sourceBubbleId="bubble-001",
                        textOriginal="original japanese",
                        textEdited="cleaned japanese",
                        order=0,
                        kind="dialogue",
                        speaker="Hero",
                    )
                ],
            )
        ]
    )

    return workspace_root, project_dir


def test_translate_command_stores_translation_and_script_layers_separately(
    tmp_path: Path,
    monkeypatch,
) -> None:
    workspace_root, project_dir = create_project_with_reviewed_frame(tmp_path)
    overrides_file = tmp_path / "script-overrides.json"
    overrides_file.write_text(
        json.dumps(
            [
                {
                    "sourceBubbleId": "bubble-001",
                    "voiceText": "Longer spoken line for VO",
                    "subtitleText": "Short subtitle",
                }
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        translation_service,
        "get_translation_service",
        lambda: FakeTranslationService(),
    )

    result = runner.invoke(
        app,
        [
            "translate",
            "demo-001",
            "--target-language",
            "zh",
            "--overrides-file",
            str(overrides_file),
            "--workspace-root",
            str(workspace_root),
        ],
    )

    assert result.exit_code == 0, result.stdout

    frames_payload = json.loads((project_dir / "script" / "frames.json").read_text(encoding="utf-8"))
    assert frames_payload[0]["reviewedBubbles"][0]["textEdited"] == "cleaned japanese"

    script_payload = json.loads((project_dir / "script" / "script.json").read_text(encoding="utf-8"))
    assert script_payload == [
        {
            "id": "script-bubble-001",
            "frameId": "frame-001",
            "sourceBubbleId": "bubble-001",
            "sourceText": "cleaned japanese",
            "translatedText": "zh:cleaned japanese",
            "voiceText": "Longer spoken line for VO",
            "subtitleText": "Short subtitle",
            "kind": "dialogue",
            "speaker": "Hero",
        }
    ]
