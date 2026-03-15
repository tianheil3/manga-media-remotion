import json
from pathlib import Path
import sys

from PIL import Image, ImageDraw
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


class SizeAwareMangaOcr:
    def __call__(self, image) -> str:
        if isinstance(image, (str, Path)):
            image = Image.open(image)

        width, _height = image.size
        return "left bubble" if width >= 45 else "right bubble"


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


def create_localized_text_image(image_path: Path) -> None:
    image = Image.new("L", (180, 120), color=255)
    draw = ImageDraw.Draw(image)

    for offset in (0, 10, 20):
        draw.rectangle((124, 14 + offset, 140, 20 + offset), fill=0)

    for offset in (0, 12, 24, 36):
        draw.rectangle((24, 50 + offset, 70, 58 + offset), fill=0)

    image.save(image_path)


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


def test_manga_ocr_engine_localizes_multiple_bubbles_with_real_geometry(tmp_path: Path) -> None:
    image_path = tmp_path / "localized-page.png"
    create_localized_text_image(image_path)

    engine = ocr_service.MangaOcrEngine.__new__(ocr_service.MangaOcrEngine)
    engine._engine = SizeAwareMangaOcr()

    bubbles = engine.extract_bubbles(image_path)

    assert len(bubbles) == 2

    left_bubble, right_bubble = sorted(bubbles, key=lambda bubble: bubble["bbox"]["x"])

    assert left_bubble["text"] == "left bubble"
    assert left_bubble["bbox"]["x"] < 40
    assert left_bubble["bbox"]["y"] > 40
    assert left_bubble["bbox"]["w"] > 35
    assert left_bubble["bbox"]["h"] > 35

    assert right_bubble["text"] == "right bubble"
    assert right_bubble["bbox"]["x"] > 110
    assert right_bubble["bbox"]["y"] < 30
    assert right_bubble["bbox"]["w"] > 10
    assert right_bubble["bbox"]["h"] > 20

    assert all(bubble["bbox"] != {"x": 0, "y": 0, "w": 1, "h": 1} for bubble in bubbles)


def test_manga_ocr_engine_assigns_ids_in_reading_order(tmp_path: Path, monkeypatch) -> None:
    image_path = tmp_path / "localized-page.png"
    create_localized_text_image(image_path)

    engine = ocr_service.MangaOcrEngine.__new__(ocr_service.MangaOcrEngine)
    engine._engine = SizeAwareMangaOcr()

    monkeypatch.setattr(
        ocr_service,
        "_localize_bubble_regions",
        lambda image: [
            {"x": 24, "y": 50, "w": 50, "h": 44},
            {"x": 124, "y": 14, "w": 16, "h": 26},
        ],
    )

    normalized_bubbles = ocr_service.normalize_bubbles(engine.extract_bubbles(image_path))

    assert [bubble.id for bubble in normalized_bubbles] == ["bubble-001", "bubble-002"]
    assert [bubble.text for bubble in normalized_bubbles] == ["right bubble", "left bubble"]
    assert [bubble.order for bubble in normalized_bubbles] == [0, 1]


def test_review_command_accepts_multi_bubble_ocr_output(tmp_path: Path, monkeypatch) -> None:
    workspace_root = create_project_with_images(tmp_path)
    project_dir = workspace_root / "demo-001"

    monkeypatch.setattr(ocr_service, "get_ocr_engine", lambda: FakeOcrEngine())
    ocr_result = runner.invoke(
        app,
        ["ocr", "demo-001", "--workspace-root", str(workspace_root)],
    )
    assert ocr_result.exit_code == 0, ocr_result.stdout

    review_file = tmp_path / "frame-001-review.json"
    review_file.write_text(
        json.dumps(
            [
                {
                    "sourceBubbleId": "right",
                    "textEdited": "Narrator line",
                    "order": 0,
                    "kind": "narration",
                    "speaker": "Narrator",
                },
                {
                    "sourceBubbleId": "left",
                    "textEdited": "Character line",
                    "order": 1,
                    "kind": "dialogue",
                    "speaker": "Hero",
                },
            ]
        ),
        encoding="utf-8",
    )

    review_result = runner.invoke(
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

    assert review_result.exit_code == 0, review_result.stdout

    frames_payload = json.loads((project_dir / "script" / "frames.json").read_text(encoding="utf-8"))
    assert [bubble["id"] for bubble in frames_payload[0]["bubbles"]] == ["right", "left"]
    assert frames_payload[0]["reviewedBubbles"] == [
        {
            "id": "review-right",
            "sourceBubbleId": "right",
            "textOriginal": "right",
            "textEdited": "Narrator line",
            "order": 0,
            "kind": "narration",
            "speaker": "Narrator",
        },
        {
            "id": "review-left",
            "sourceBubbleId": "left",
            "textOriginal": "left",
            "textEdited": "Character line",
            "order": 1,
            "kind": "dialogue",
            "speaker": "Hero",
        },
    ]
