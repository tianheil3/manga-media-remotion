import json
from pathlib import Path
import sys

from typer.testing import CliRunner

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.cli.app.main import app
import apps.cli.app.services.ocr_service as ocr_service

runner = CliRunner()

PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\rIHDR"
    b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00"
    b"\x90wS\xde"
    b"\x00\x00\x00\x0cIDAT\x08\xd7c\xf8\xff\xff?\x00\x05\xfe\x02\xfeA\xd9\xa3\x1d"
    b"\x00\x00\x00\x00IEND\xaeB`\x82"
)


class FakeOcrEngine:
    def extract_bubbles(self, image_path: Path) -> list[dict[str, object]]:
        if image_path.name == "001.png":
            return [
                {
                    "id": "bubble-a",
                    "text": "original-a",
                    "bbox": {"x": 50, "y": 10, "w": 5, "h": 5},
                    "confidence": 0.9,
                    "language": "ja",
                },
                {
                    "id": "bubble-b",
                    "text": "original-b",
                    "bbox": {"x": 20, "y": 10, "w": 5, "h": 5},
                    "confidence": 0.8,
                    "language": "ja",
                },
            ]

        return [
            {
                "id": "bubble-c",
                "text": "original-c",
                "bbox": {"x": 40, "y": 10, "w": 5, "h": 5},
                "confidence": 0.9,
                "language": "ja",
            }
        ]


def create_project_with_ocr(tmp_path: Path, monkeypatch) -> tuple[Path, Path]:
    workspace_root = tmp_path / "workspace"

    result = runner.invoke(
        app,
        [
            "new",
            "demo-001",
            "--title",
            "Demo Project",
            "--workspace-root",
            str(workspace_root),
        ],
    )
    assert result.exit_code == 0, result.stdout

    source_one = tmp_path / "page-001.png"
    source_two = tmp_path / "page-002.png"
    source_one.write_bytes(PNG_BYTES)
    source_two.write_bytes(PNG_BYTES)

    result = runner.invoke(
        app,
        [
            "import-images",
            "demo-001",
            str(source_one),
            str(source_two),
            "--workspace-root",
            str(workspace_root),
        ],
    )
    assert result.exit_code == 0, result.stdout

    monkeypatch.setattr(ocr_service, "get_ocr_engine", lambda: FakeOcrEngine())
    result = runner.invoke(
        app,
        ["ocr", "demo-001", "--workspace-root", str(workspace_root)],
    )
    assert result.exit_code == 0, result.stdout

    return workspace_root, workspace_root / "demo-001"


def test_review_command_updates_reviewed_bubbles_without_mutating_ocr(
    tmp_path: Path,
    monkeypatch,
) -> None:
    workspace_root, project_dir = create_project_with_ocr(tmp_path, monkeypatch)
    review_file = tmp_path / "frame-001-review.json"
    review_file.write_text(
        json.dumps(
            [
                {
                    "sourceBubbleId": "bubble-b",
                    "textEdited": "Narrator line",
                    "order": 0,
                    "kind": "narration",
                    "speaker": "Narrator",
                },
                {
                    "sourceBubbleId": "bubble-a",
                    "textEdited": "Character line",
                    "order": 1,
                    "kind": "dialogue",
                    "speaker": "Hero",
                },
            ]
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "review",
            "demo-001",
            "frame-001",
            "--review-file",
            str(review_file),
            "--workspace-root",
            str(workspace_root),
        ],
    )

    assert result.exit_code == 0, result.stdout

    frames_payload = json.loads((project_dir / "script" / "frames.json").read_text(encoding="utf-8"))
    frame_payload = frames_payload[0]

    assert [bubble["text"] for bubble in frame_payload["bubbles"]] == ["original-a", "original-b"]
    assert frame_payload["reviewedBubbles"] == [
        {
            "id": "review-bubble-b",
            "sourceBubbleId": "bubble-b",
            "textOriginal": "original-b",
            "textEdited": "Narrator line",
            "order": 0,
            "kind": "narration",
            "speaker": "Narrator",
        },
        {
            "id": "review-bubble-a",
            "sourceBubbleId": "bubble-a",
            "textOriginal": "original-a",
            "textEdited": "Character line",
            "order": 1,
            "kind": "dialogue",
            "speaker": "Hero",
        },
    ]


def test_skipped_review_pages_remain_editable_later(tmp_path: Path, monkeypatch) -> None:
    workspace_root, project_dir = create_project_with_ocr(tmp_path, monkeypatch)

    result = runner.invoke(
        app,
        [
            "review",
            "demo-001",
            "frame-002",
            "--skip",
            "--workspace-root",
            str(workspace_root),
        ],
    )

    assert result.exit_code == 0, result.stdout
    frames_payload = json.loads((project_dir / "script" / "frames.json").read_text(encoding="utf-8"))
    assert frames_payload[1]["reviewedBubbles"] == []

    review_file = tmp_path / "frame-002-review.json"
    review_file.write_text(
        json.dumps(
            [
                {
                    "sourceBubbleId": "bubble-c",
                    "textEdited": "Later edit",
                    "order": 0,
                    "kind": "sfx",
                }
            ]
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "review",
            "demo-001",
            "frame-002",
            "--review-file",
            str(review_file),
            "--workspace-root",
            str(workspace_root),
        ],
    )

    assert result.exit_code == 0, result.stdout

    frames_payload = json.loads((project_dir / "script" / "frames.json").read_text(encoding="utf-8"))
    assert frames_payload[1]["reviewedBubbles"] == [
        {
            "id": "review-bubble-c",
            "sourceBubbleId": "bubble-c",
            "textOriginal": "original-c",
            "textEdited": "Later edit",
            "order": 0,
            "kind": "sfx",
            "speaker": None,
        }
    ]
