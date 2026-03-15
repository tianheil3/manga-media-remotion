import io
from pathlib import Path
import sys
from urllib import error

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.cli.app.services.translation_service import (  # noqa: E402
    DeepLTranslationService,
    TranslationServiceError,
    get_translation_service,
)


def test_deepl_translation_service_returns_translated_text() -> None:
    seen_request: dict[str, object] = {}

    def fake_transport(request):
        seen_request["url"] = request.full_url
        seen_request["body"] = request.data.decode("utf-8")
        seen_request["headers"] = dict(request.header_items())
        return b'{"translations":[{"text":"\xe7\xbf\xbb\xe8\xaf\x91\xe5\x90\x8e"}]}'

    service = DeepLTranslationService(
        base_url="https://api-free.deepl.com/v2/translate",
        api_key="secret-token",
        transport=fake_transport,
    )

    translated_text = service.translate_text("cleaned japanese", "ja", "zh")

    assert translated_text == "翻译后"
    assert seen_request["url"] == "https://api-free.deepl.com/v2/translate"
    assert "text=cleaned+japanese" in seen_request["body"]
    assert "source_lang=JA" in seen_request["body"]
    assert "target_lang=ZH" in seen_request["body"]
    assert seen_request["headers"]["Authorization"] == "DeepL-Auth-Key secret-token"


def test_get_translation_service_builds_deepl_client_from_env(monkeypatch) -> None:
    monkeypatch.setenv("TRANSLATION_PROVIDER", "deepl")
    monkeypatch.setenv("DEEPL_API_KEY", "secret-token")
    monkeypatch.setenv("DEEPL_BASE_URL", "https://example.invalid/v2/translate")

    service = get_translation_service()

    assert isinstance(service, DeepLTranslationService)
    assert service.base_url == "https://example.invalid/v2/translate"
    assert service.api_key == "secret-token"


def test_get_translation_service_requires_deepl_api_key(monkeypatch) -> None:
    monkeypatch.setenv("TRANSLATION_PROVIDER", "deepl")
    monkeypatch.delenv("DEEPL_API_KEY", raising=False)
    monkeypatch.delenv("DEEPL_BASE_URL", raising=False)

    with pytest.raises(
        TranslationServiceError,
        match="Set TRANSLATION_PROVIDER=deepl and DEEPL_API_KEY",
    ):
        get_translation_service()


def test_get_translation_service_rejects_unsupported_provider(monkeypatch) -> None:
    monkeypatch.setenv("TRANSLATION_PROVIDER", "bogus")
    monkeypatch.delenv("DEEPL_API_KEY", raising=False)

    with pytest.raises(
        TranslationServiceError,
        match="Unsupported translation provider 'bogus'. Set TRANSLATION_PROVIDER=deepl.",
    ):
        get_translation_service()


def test_deepl_translation_service_includes_provider_error_message_from_http_error() -> None:
    def failing_transport(request):
        raise error.HTTPError(
            request.full_url,
            456,
            "Quota Exceeded",
            hdrs=None,
            fp=io.BytesIO(b'{"message":"Quota exceeded, check billing"}'),
        )

    service = DeepLTranslationService(
        base_url="https://api-free.deepl.com/v2/translate",
        api_key="secret-token",
        transport=failing_transport,
    )

    with pytest.raises(
        TranslationServiceError,
        match="Quota exceeded, check billing",
    ):
        service.translate_text("cleaned japanese", "ja", "zh")
