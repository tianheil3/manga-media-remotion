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


def validate_ocr_setup():
    try:
        from manga_ocr import MangaOcr
    except ImportError as exc:
        raise RuntimeError(
            "MangaOCR is not installed. Install the `manga-ocr` Python package before running OCR or `doctor`."
        ) from exc

    return MangaOcr


class MangaOcrEngine:
    def __init__(self) -> None:
        self._engine = validate_ocr_setup()()

    def extract_bubbles(self, image_path: Path) -> list[dict[str, object]]:
        image = _load_image(image_path)
        localized_bubbles = _extract_localized_bubbles(self._engine, image)
        if localized_bubbles:
            return localized_bubbles

        return _extract_full_page_bubble(self._engine, image)


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


def _load_image(image_path: Path):
    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("OCR localization requires Pillow. Install Pillow before running OCR.") from exc

    with Image.open(image_path) as source_image:
        return source_image.convert("RGB")


def _extract_localized_bubbles(engine, image) -> list[dict[str, object]]:
    localized_bubbles: list[dict[str, object]] = []

    for bbox in _localize_bubble_regions(image):
        crop = image.crop((bbox["x"], bbox["y"], bbox["x"] + bbox["w"], bbox["y"] + bbox["h"]))
        text = str(engine(crop)).strip()
        if not text:
            continue

        localized_bubbles.append(
            {
                "text": text,
                "bbox": bbox,
                "confidence": 1.0,
                "language": "ja",
            }
        )

    return localized_bubbles


def _extract_full_page_bubble(engine, image) -> list[dict[str, object]]:
    text = str(engine(image)).strip()
    if not text:
        return []

    width, height = image.size
    return [
        {
            "text": text,
            "bbox": {"x": 0, "y": 0, "w": width, "h": height},
            "confidence": 1.0,
            "language": "ja",
        }
    ]


def _localize_bubble_regions(image) -> list[dict[str, int]]:
    try:
        import cv2
        import numpy as np
    except ImportError as exc:
        raise RuntimeError(
            "OCR localization requires opencv-python and numpy. Install the local render dependencies before running OCR."
        ) from exc

    grayscale = np.array(image.convert("L"))
    _, mask = cv2.threshold(grayscale, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    kernel_size = min(25, max(5, min(image.size) // 40))
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, kernel_size))
    dilated = cv2.dilate(mask, kernel, iterations=1)

    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    min_width = max(10, image.width // 100)
    min_height = max(10, image.height // 100)
    min_foreground_pixels = max(20, (image.width * image.height) // 5000)
    padding = max(2, min(image.size) // 200)

    localized_regions: list[dict[str, int]] = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        foreground_pixels = int(cv2.countNonZero(mask[y : y + h, x : x + w]))
        if w < min_width or h < min_height or foreground_pixels < min_foreground_pixels:
            continue

        x0 = max(0, x - padding)
        y0 = max(0, y - padding)
        x1 = min(image.width, x + w + padding)
        y1 = min(image.height, y + h + padding)
        localized_regions.append({"x": x0, "y": y0, "w": x1 - x0, "h": y1 - y0})

    return localized_regions
