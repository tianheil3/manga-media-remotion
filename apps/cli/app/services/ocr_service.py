import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

from apps.api.app.models.frame import BoundingBox, Frame, OcrBubble
from apps.api.app.services.file_store import FileStore
from apps.cli.app.services.reading_order import sort_bubbles


class OcrEngine(Protocol):
    def extract_bubbles(self, image_path: Path) -> list[dict[str, object]]:
        ...


class MangaOcrEngine:
    def __init__(self) -> None:
        try:
            from manga_ocr import MangaOcr
        except ImportError as exc:
            raise RuntimeError(
                "MangaOCR is not installed. Install the `manga-ocr` Python package before running OCR."
            ) from exc

        self._engine = MangaOcr()

    def extract_bubbles(self, image_path: Path) -> list[dict[str, object]]:
        text = str(self._engine(str(image_path))).strip()
        if not text:
            return []

        return [
            {
                "id": "bubble-001",
                "text": text,
                "bbox": {"x": 0, "y": 0, "w": 1, "h": 1},
                "confidence": 1.0,
                "language": "ja",
            }
        ]


def get_ocr_engine() -> OcrEngine:
    return MangaOcrEngine()


def run_ocr(project_dir: Path, engine: OcrEngine | None = None) -> list[Frame]:
    store = FileStore(project_dir)
    frames = store.load_frames()
    if not frames:
        raise ValueError("No imported frames found. Run import-images first.")

    ocr_engine = engine or get_ocr_engine()
    updated_frames: list[Frame] = []

    for frame in frames:
        image_path = project_dir / frame.image
        raw_bubbles = ocr_engine.extract_bubbles(image_path)
        normalized_bubbles = normalize_bubbles(raw_bubbles)

        ocr_output_path = project_dir / frame.ocr_file
        ocr_output_path.parent.mkdir(parents=True, exist_ok=True)
        ocr_output_path.write_text(
            json.dumps(
                [bubble.model_dump(mode="json") for bubble in normalized_bubbles],
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        updated_frames.append(frame.model_copy(update={"bubbles": normalized_bubbles}))

    store.save_frames(updated_frames)
    project = store.load_project()
    project.updated_at = _utc_timestamp()
    store.save_project(project)

    return updated_frames


def normalize_bubbles(raw_bubbles: list[dict[str, object]]) -> list[OcrBubble]:
    normalized: list[OcrBubble] = []
    for index, bubble in enumerate(sort_bubbles(raw_bubbles), start=1):
        bbox = bubble.get("bbox")
        if not isinstance(bbox, dict):
            raise ValueError("OCR bubble is missing bbox data")

        normalized.append(
            OcrBubble(
                id=str(bubble.get("id") or f"bubble-{index:03d}"),
                text=str(bubble.get("text") or ""),
                bbox=BoundingBox(
                    x=float(bbox["x"]),
                    y=float(bbox["y"]),
                    w=float(bbox["w"]),
                    h=float(bbox["h"]),
                ),
                order=int(bubble["order"]),
                confidence=float(bubble.get("confidence", 1.0)),
                language=str(bubble.get("language", "ja")),
            )
        )

    return normalized


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
