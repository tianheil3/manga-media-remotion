from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.api.app.integrations.moyin_tts import MoyinTtsClient, MoyinTtsError


def test_moyin_tts_client_returns_audio_bytes() -> None:
    seen_request: dict[str, object] = {}

    def fake_transport(request):
        seen_request["url"] = request.full_url
        seen_request["body"] = request.data.decode("utf-8")
        seen_request["headers"] = dict(request.header_items())
        return b"FAKE-WAV"

    client = MoyinTtsClient(
        base_url="https://example.invalid/tts",
        api_key="secret-token",
        transport=fake_transport,
    )

    audio_bytes = client.synthesize("hello world", "narrator-default")

    assert audio_bytes == b"FAKE-WAV"
    assert seen_request["url"] == "https://example.invalid/tts"
    assert '"text": "hello world"' in seen_request["body"]
    assert '"voicePreset": "narrator-default"' in seen_request["body"]
    assert seen_request["headers"]["Authorization"] == "Bearer secret-token"


def test_moyin_tts_client_wraps_provider_errors() -> None:
    def failing_transport(request):
        raise OSError("network down")

    client = MoyinTtsClient(
        base_url="https://example.invalid/tts",
        api_key="secret-token",
        transport=failing_transport,
    )

    with pytest.raises(MoyinTtsError, match="Moyin TTS request failed: network down"):
        client.synthesize("hello world", "narrator-default")
