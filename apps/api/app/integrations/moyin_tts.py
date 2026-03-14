import json
import os
from typing import Callable
from urllib import request


class MoyinTtsError(RuntimeError):
    """Raised when the Moyin TTS provider cannot synthesize audio."""


class MoyinTtsClient:
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
    def from_env(cls) -> "MoyinTtsClient":
        base_url = os.environ.get("MOYIN_TTS_BASE_URL")
        api_key = os.environ.get("MOYIN_TTS_API_KEY")
        if not base_url or not api_key:
            raise MoyinTtsError(
                "Moyin TTS is not configured. Set MOYIN_TTS_BASE_URL and MOYIN_TTS_API_KEY."
            )

        return cls(base_url=base_url, api_key=api_key)

    def synthesize(self, text: str, voice_preset: str) -> bytes:
        payload = json.dumps({"text": text, "voicePreset": voice_preset}).encode("utf-8")
        req = request.Request(
            self.base_url,
            data=payload,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            return self.transport(req)
        except Exception as exc:  # pragma: no cover - exercised via tests
            raise MoyinTtsError(f"Moyin TTS request failed: {exc}") from exc

    @staticmethod
    def _default_transport(req: request.Request) -> bytes:
        with request.urlopen(req) as response:
            return response.read()
