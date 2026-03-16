import io
import json
from pathlib import Path
import sys
from urllib import error

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.cli.app.services.translation_service import (  # noqa: E402
    MangaImageTranslatorTranslationService,
    TranslationServiceError,
    get_translation_service,
)


def test_manga_image_translator_translation_service_returns_translated_text() -> None:
    seen_request: dict[str, object] = {}

    def fake_transport(request):
        seen_request["url"] = request.full_url
        seen_request["body"] = json.loads(request.data.decode("utf-8"))
        seen_request["headers"] = dict(request.header_items())
        return b'{"translatedText":"\xe7\xbf\xbb\xe8\xaf\x91\xe5\x90\x8e"}'

    service = MangaImageTranslatorTranslationService(
        base_url="https://mit.example.invalid",
        translate_path="/translate/text",
        transport=fake_transport,
    )

    translated_text = service.translate_text("cleaned japanese", "ja", "zh")

    assert translated_text == "翻译后"
    assert seen_request["url"] == "https://mit.example.invalid/translate/text"
    assert seen_request["body"] == {
        "sourceLanguage": "ja",
        "targetLanguage": "zh",
        "text": "cleaned japanese",
    }
    assert seen_request["headers"]["Content-type"] == "application/json"


def test_get_translation_service_builds_mit_client_from_env(monkeypatch) -> None:
    monkeypatch.setenv("MANGA_IMAGE_TRANSLATOR_BASE_URL", "https://mit.example.invalid")
    monkeypatch.setenv("MANGA_IMAGE_TRANSLATOR_TRANSLATE_PATH", "/translate/text")
    monkeypatch.setenv("MANGA_IMAGE_TRANSLATOR_API_KEY", "secret-token")

    service = get_translation_service()

    assert isinstance(service, MangaImageTranslatorTranslationService)
    assert service.base_url == "https://mit.example.invalid"
    assert service.translate_path == "/translate/text"
    assert service.api_key == "secret-token"


def test_get_translation_service_requires_service_base_url(monkeypatch) -> None:
    monkeypatch.delenv("MANGA_IMAGE_TRANSLATOR_BASE_URL", raising=False)
    monkeypatch.delenv("MANGA_IMAGE_TRANSLATOR_TRANSLATE_PATH", raising=False)
    monkeypatch.delenv("MANGA_IMAGE_TRANSLATOR_API_KEY", raising=False)

    with pytest.raises(
        TranslationServiceError,
        match="Set MANGA_IMAGE_TRANSLATOR_BASE_URL",
    ):
        get_translation_service()


def test_manga_image_translator_translation_service_includes_provider_error_message_from_http_error() -> None:
    def failing_transport(request):
        raise error.HTTPError(
            request.full_url,
            503,
            "Service Unavailable",
            hdrs=None,
            fp=io.BytesIO(b'{"detail":"translator worker unavailable"}'),
        )

    service = MangaImageTranslatorTranslationService(
        base_url="https://mit.example.invalid",
        translate_path="/translate/text",
        transport=failing_transport,
    )

    with pytest.raises(
        TranslationServiceError,
        match="translator worker unavailable",
    ):
        service.translate_text("cleaned japanese", "ja", "zh")
