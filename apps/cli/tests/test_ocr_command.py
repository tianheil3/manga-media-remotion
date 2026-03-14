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
                    "id": "left",
                    "text": "left",
                    "bbox": {"x": 10, "y": 20, "w": 5, "h": 5},
                    "confidence": 0.8,
                    "language": "ja",
                },
                {
                    "id": "right",
                    "text": "right",
                    "bbox": {"x": 50, "y": 10, "w": 5, "h": 5},
                    "confidence": 0.9,
                    "language": "ja",
                },
            ]

        return [
            {
                "id": "solo",
                "text": "solo",
                "bbox": {"x": 12, "y": 12, "w": 5, "h": 5},
                "confidence": 0.95,
                "language": "ja",
            }
        ]


def create_project_with_images(tmp_path: Path) -> Path:
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

    return workspace_root


def test_ocr_command_writes_per_image_output_and_updates_frames(
    tmp_path: Path,
    monkeypatch,
) -> None:
    workspace_root = create_project_with_images(tmp_path)
    project_dir = workspace_root / "demo-001"

    monkeypatch.setattr(ocr_service, "get_ocr_engine", lambda: FakeOcrEngine())

    result = runner.invoke(
        app,
        ["ocr", "demo-001", "--workspace-root", str(workspace_root)],
    )

    assert result.exit_code == 0, result.stdout

    ocr_payload = json.loads((project_dir / "ocr" / "001.json").read_text(encoding="utf-8"))
    assert [bubble["id"] for bubble in ocr_payload] == ["right", "left"]
    assert [bubble["order"] for bubble in ocr_payload] == [0, 1]

    frames_payload = json.loads((project_dir / "script" / "frames.json").read_text(encoding="utf-8"))
    assert [bubble["id"] for bubble in frames_payload[0]["bubbles"]] == ["right", "left"]
    assert frames_payload[1]["bubbles"][0]["id"] == "solo"
