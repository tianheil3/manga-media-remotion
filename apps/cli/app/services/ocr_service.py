import json
import mimetypes
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Protocol
from urllib import error, request

from apps.api.app.models.frame import BoundingBox, Frame, OcrBubble
from apps.api.app.services.file_store import FileStore
from apps.cli.app.services.reading_order import sort_bubbles


class OcrEngine(Protocol):
    def extract_bubbles(self, image_path: Path) -> list[dict[str, object]]:
        ...


def validate_ocr_setup() -> "MangaImageTranslatorOcrEngine":
    return MangaImageTranslatorOcrEngine.from_env()


class MangaImageTranslatorOcrEngine:
    def __init__(
        self,
        *,
        base_url: str,
        ocr_path: str,
        api_key: str | None = None,
        transport: Callable[[request.Request], bytes] | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.ocr_path = ocr_path
        self.api_key = api_key
        self.transport = transport or self._default_transport

    @classmethod
    def from_env(cls) -> "MangaImageTranslatorOcrEngine":
        base_url = os.environ.get("MANGA_IMAGE_TRANSLATOR_BASE_URL", "").strip()
        if not base_url:
            raise RuntimeError(
                "Manga Image Translator OCR is not configured. "
                "Set MANGA_IMAGE_TRANSLATOR_BASE_URL; optionally "
                "MANGA_IMAGE_TRANSLATOR_OCR_PATH and MANGA_IMAGE_TRANSLATOR_API_KEY."
            )

        ocr_path = os.environ.get("MANGA_IMAGE_TRANSLATOR_OCR_PATH", "/translate/with-form/json").strip()
        if not ocr_path:
            ocr_path = "/translate/with-form/json"

        api_key = os.environ.get("MANGA_IMAGE_TRANSLATOR_API_KEY", "").strip() or None
        return cls(base_url=base_url, ocr_path=ocr_path, api_key=api_key)

    def extract_bubbles(self, image_path: Path) -> list[dict[str, object]]:
        content_type, payload = _encode_multipart_form_data(
            fields={
                "config": json.dumps(
                    {
                        "translator": {"translator": "none"},
                        "render": {"direction": "none"},
                        "inpainter": {"inpainter": "none"},
                    }
                )
            },
            files={
                "image": (
                    image_path.name,
                    image_path.read_bytes(),
                    mimetypes.guess_type(image_path.name)[0] or "application/octet-stream",
                )
            },
        )
        headers = {"Content-Type": content_type}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        req = request.Request(
            self._build_url(self.ocr_path),
            data=payload,
            headers=headers,
            method="POST",
        )

        try:
            response_payload = self.transport(req)
        except error.HTTPError as exc:
            raise RuntimeError(self._format_http_error(exc)) from exc
        except Exception as exc:  # pragma: no cover - exercised in command tests
            raise RuntimeError(f"Manga Image Translator OCR request failed: {exc}") from exc

        try:
            response = json.loads(response_payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Manga Image Translator OCR response was invalid: {exc}") from exc

        return self._extract_bubbles(response)

    def _build_url(self, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path

        return f"{self.base_url}/{path.lstrip('/')}"

    @staticmethod
    def _default_transport(req: request.Request) -> bytes:
        with request.urlopen(req) as response:
            return response.read()

    def _extract_bubbles(self, response: object) -> list[dict[str, object]]:
        if isinstance(response, dict):
            translations = response.get("translations")
            if isinstance(translations, list):
                return [self._bubble_from_translation(item) for item in translations]

            bubbles = response.get("bubbles")
            if isinstance(bubbles, list):
                return [self._bubble_from_service_payload(item) for item in bubbles]

        if isinstance(response, list):
            return [self._bubble_from_service_payload(item) for item in response]

        raise RuntimeError("Manga Image Translator OCR response did not include bubbles.")

    def _bubble_from_translation(self, item: object) -> dict[str, object]:
        if not isinstance(item, dict):
            raise RuntimeError("Manga Image Translator OCR returned an invalid translation item.")

        min_x = int(item["minX"])
        min_y = int(item["minY"])
        max_x = int(item["maxX"])
        max_y = int(item["maxY"])
        text_payload = item.get("text")
        text = self._extract_text(text_payload)
        language = self._extract_language(text_payload)

        return {
            "text": text,
            "bbox": {"x": min_x, "y": min_y, "w": max_x - min_x, "h": max_y - min_y},
            "confidence": float(item.get("prob", 1.0)),
            "language": language,
        }

    def _bubble_from_service_payload(self, item: object) -> dict[str, object]:
        if not isinstance(item, dict):
            raise RuntimeError("Manga Image Translator OCR returned an invalid bubble item.")

        bbox = item.get("bbox")
        if not isinstance(bbox, dict):
            raise RuntimeError("Manga Image Translator OCR bubble is missing bbox data.")

        text = item.get("text")
        if not isinstance(text, str):
            raise RuntimeError("Manga Image Translator OCR bubble is missing text.")

        return {
            "id": item.get("id"),
            "text": text,
            "bbox": bbox,
            "confidence": float(item.get("confidence", 1.0)),
            "language": self._normalize_language(item.get("language")),
        }

    @staticmethod
    def _extract_text(text_payload: object) -> str:
        if isinstance(text_payload, str):
            return text_payload

        if isinstance(text_payload, dict):
            for value in text_payload.values():
                if isinstance(value, str) and value:
                    return value

        raise RuntimeError("Manga Image Translator OCR response did not include source text.")

    def _extract_language(self, text_payload: object) -> str:
        if isinstance(text_payload, dict):
            for key in text_payload:
                normalized = self._normalize_language(key)
                if normalized:
                    return normalized

        return "ja"

    @staticmethod
    def _normalize_language(language: object) -> str:
        if not isinstance(language, str) or not language.strip():
            return "ja"

        normalized = language.strip().lower()
        if normalized in {"ja", "jpn", "jp", "ja-jp"}:
            return "ja"
        if normalized in {"zh", "chs", "cht", "zh-cn", "zh-tw"}:
            return "zh"
        if normalized in {"en", "eng", "en-us", "en-gb"}:
            return "en"

        return "ja"

    @staticmethod
    def _format_http_error(exc: error.HTTPError) -> str:
        detail = None
        if exc.fp is not None:
            try:
                payload = exc.fp.read()
                response = json.loads(payload.decode("utf-8"))
                for key in ("detail", "message", "error"):
                    value = response.get(key)
                    if isinstance(value, str):
                        detail = value
                        break
            except (OSError, UnicodeDecodeError, json.JSONDecodeError, AttributeError):
                detail = None

        if detail:
            return f"Manga Image Translator OCR request failed: {detail}"

        return f"Manga Image Translator OCR request failed: {exc}"


def get_ocr_engine() -> OcrEngine:
    return MangaImageTranslatorOcrEngine.from_env()


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
                order=int(bubble.get("order", index - 1)),
                confidence=float(bubble.get("confidence", 1.0)),
                language=MangaImageTranslatorOcrEngine._normalize_language(bubble.get("language")),
            )
        )

    return normalized


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _encode_multipart_form_data(
    *,
    fields: dict[str, str],
    files: dict[str, tuple[str, bytes, str]],
) -> tuple[str, bytes]:
    boundary = f"----codex-boundary-{uuid.uuid4().hex}"
    lines: list[bytes] = []

    for name, value in fields.items():
        lines.extend(
            [
                f"--{boundary}".encode("utf-8"),
                f'Content-Disposition: form-data; name="{name}"'.encode("utf-8"),
                b"",
                value.encode("utf-8"),
            ]
        )

    for name, (filename, content, content_type) in files.items():
        lines.extend(
            [
                f"--{boundary}".encode("utf-8"),
                f'Content-Disposition: form-data; name="{name}"; filename="{filename}"'.encode("utf-8"),
                f"Content-Type: {content_type}".encode("utf-8"),
                b"",
                content,
            ]
        )

    lines.append(f"--{boundary}--".encode("utf-8"))
    lines.append(b"")
    payload = b"\r\n".join(lines)
    return f"multipart/form-data; boundary={boundary}", payload
