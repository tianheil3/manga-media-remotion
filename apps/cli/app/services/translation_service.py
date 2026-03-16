import json
import os
from typing import Callable, Protocol
from urllib import error, request


class TranslationServiceError(RuntimeError):
    """Raised when translation provider configuration or requests fail."""


class TranslationService(Protocol):
    def translate_text(self, text: str, source_language: str, target_language: str) -> str:
        ...


class MangaImageTranslatorTranslationService:
    def __init__(
        self,
        *,
        base_url: str,
        translate_path: str,
        api_key: str | None = None,
        transport: Callable[[request.Request], bytes] | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.translate_path = translate_path
        self.api_key = api_key
        self.transport = transport or self._default_transport

    @classmethod
    def from_env(cls) -> "MangaImageTranslatorTranslationService":
        base_url = os.environ.get("MANGA_IMAGE_TRANSLATOR_BASE_URL", "").strip()
        if not base_url:
            raise TranslationServiceError(
                "Manga Image Translator translation is not configured. "
                "Set MANGA_IMAGE_TRANSLATOR_BASE_URL; optionally "
                "MANGA_IMAGE_TRANSLATOR_TRANSLATE_PATH and MANGA_IMAGE_TRANSLATOR_API_KEY."
            )

        translate_path = os.environ.get("MANGA_IMAGE_TRANSLATOR_TRANSLATE_PATH", "/translate/text").strip()
        if not translate_path:
            translate_path = "/translate/text"

        api_key = os.environ.get("MANGA_IMAGE_TRANSLATOR_API_KEY", "").strip() or None
        return cls(base_url=base_url, translate_path=translate_path, api_key=api_key)

    def translate_text(self, text: str, source_language: str, target_language: str) -> str:
        payload = json.dumps(
            {
                "text": text,
                "sourceLanguage": source_language,
                "targetLanguage": target_language,
            }
        ).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        req = request.Request(
            self._build_url(self.translate_path),
            data=payload,
            headers=headers,
            method="POST",
        )

        try:
            response_payload = self.transport(req)
        except error.HTTPError as exc:
            raise TranslationServiceError(self._format_http_error(exc)) from exc
        except Exception as exc:  # pragma: no cover - exercised via tests
            raise TranslationServiceError(f"Manga Image Translator request failed: {exc}") from exc

        try:
            response = json.loads(response_payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise TranslationServiceError(f"Manga Image Translator response was invalid: {exc}") from exc

        translated_text = self._extract_translated_text(response)
        if translated_text is None:
            raise TranslationServiceError("Manga Image Translator response did not include translated text.")

        return translated_text

    def _build_url(self, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path

        return f"{self.base_url}/{path.lstrip('/')}"

    @staticmethod
    def _default_transport(req: request.Request) -> bytes:
        with request.urlopen(req) as response:
            return response.read()

    @staticmethod
    def _extract_translated_text(response: object) -> str | None:
        if isinstance(response, dict):
            for key in ("translatedText", "translation", "text"):
                value = response.get(key)
                if isinstance(value, str):
                    return value

        return None

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
            return f"Manga Image Translator request failed: {detail}"

        return f"Manga Image Translator request failed: {exc}"


class DeferredFailureTranslationService:
    def __init__(self, error: TranslationServiceError) -> None:
        self.error = error

    def translate_text(self, text: str, source_language: str, target_language: str) -> str:
        raise self.error


def get_translation_service() -> TranslationService:
    return MangaImageTranslatorTranslationService.from_env()
