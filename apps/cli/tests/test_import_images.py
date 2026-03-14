import json
from pathlib import Path
import sys

from typer.testing import CliRunner

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.cli.app.main import app

runner = CliRunner()

PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\rIHDR"
    b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00"
    b"\x90wS\xde"
    b"\x00\x00\x00\x0cIDAT\x08\xd7c\xf8\xff\xff?\x00\x05\xfe\x02\xfeA\xd9\xa3\x1d"
    b"\x00\x00\x00\x00IEND\xaeB`\x82"
)


def create_project(workspace_root: Path) -> Path:
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
    return workspace_root / "demo-001"


def test_import_images_preserves_cli_order_and_writes_frame_stubs(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    project_dir = create_project(workspace_root)

    source_one = tmp_path / "page-b.png"
    source_two = tmp_path / "page-a.png"
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
    assert (project_dir / "images" / "001.png").exists()
    assert (project_dir / "images" / "002.png").exists()

    frames_payload = json.loads((project_dir / "script" / "frames.json").read_text(encoding="utf-8"))
    assert frames_payload == [
        {
            "frameId": "frame-001",
            "image": "images/001.png",
            "ocrFile": "ocr/001.json",
            "bubbles": [],
            "reviewedBubbles": [],
        },
        {
            "frameId": "frame-002",
            "image": "images/002.png",
            "ocrFile": "ocr/002.json",
            "bubbles": [],
            "reviewedBubbles": [],
        },
    ]


def test_import_images_rejects_non_image_inputs(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    create_project(workspace_root)

    not_an_image = tmp_path / "notes.txt"
    not_an_image.write_text("not an image", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "import-images",
            "demo-001",
            str(not_an_image),
            "--workspace-root",
            str(workspace_root),
        ],
    )

    assert result.exit_code == 1, result.stdout
    assert "Unsupported image file" in result.stdout
