import json
import os
from typing import Callable, Protocol
from urllib import error, parse, request


class TranslationServiceError(RuntimeError):
    """Raised when translation provider configuration or requests fail."""


class TranslationService(Protocol):
    def translate_text(self, text: str, source_language: str, target_language: str) -> str:
        ...


class DeepLTranslationService:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        transport: Callable[[request.Request], bytes] | None = None,
    ) -> None:
        self.base_url = base_url
        self.api_key = api_key
        self.transport = transport or self._default_transport

    @classmethod
    def from_env(cls) -> "DeepLTranslationService":
        api_key = os.environ.get("DEEPL_API_KEY")
        base_url = os.environ.get("DEEPL_BASE_URL", "https://api-free.deepl.com/v2/translate")
        if not api_key:
            raise TranslationServiceError(
                "DeepL translation is not configured. Set DEEPL_API_KEY and optionally DEEPL_BASE_URL."
            )

        return cls(base_url=base_url, api_key=api_key)

    def translate_text(self, text: str, source_language: str, target_language: str) -> str:
        payload = parse.urlencode(
            {
                "text": text,
                "source_lang": source_language.upper(),
                "target_lang": target_language.upper(),
            }
        ).encode("utf-8")
        req = request.Request(
            self.base_url,
            data=payload,
            headers={
                "Authorization": f"DeepL-Auth-Key {self.api_key}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            method="POST",
        )

        try:
            response_payload = self.transport(req)
        except error.HTTPError as exc:
            raise TranslationServiceError(self._format_http_error(exc)) from exc
        except Exception as exc:  # pragma: no cover - exercised via tests
            raise TranslationServiceError(f"DeepL translation request failed: {exc}") from exc

        try:
            response = json.loads(response_payload.decode("utf-8"))
            return response["translations"][0]["text"]
        except (UnicodeDecodeError, json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
            raise TranslationServiceError(f"DeepL translation response was invalid: {exc}") from exc

    @staticmethod
    def _default_transport(req: request.Request) -> bytes:
        with request.urlopen(req) as response:
            return response.read()

    @staticmethod
    def _format_http_error(exc: error.HTTPError) -> str:
        detail = None
        if exc.fp is not None:
            try:
                payload = exc.fp.read()
                response = json.loads(payload.decode("utf-8"))
                detail = response.get("message")
            except (OSError, UnicodeDecodeError, json.JSONDecodeError, AttributeError):
                detail = None

        if detail:
            return f"DeepL translation request failed: {detail}"

        return f"DeepL translation request failed: {exc}"


class DeferredFailureTranslationService:
    def __init__(self, error: TranslationServiceError) -> None:
        self.error = error

    def translate_text(self, text: str, source_language: str, target_language: str) -> str:
        raise self.error


def get_translation_service() -> TranslationService:
    provider = os.environ.get("TRANSLATION_PROVIDER", "deepl").strip().lower()
    if provider == "deepl":
        return DeepLTranslationService.from_env()

    raise TranslationServiceError(
        f"Unsupported translation provider '{provider}'. Set TRANSLATION_PROVIDER=deepl."
    )
