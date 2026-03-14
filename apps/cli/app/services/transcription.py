from pathlib import Path
from typing import Protocol


class Transcriber(Protocol):
    def transcribe(self, audio_path: Path) -> str:
        ...


def transcribe_audio(audio_path: Path, transcriber: Transcriber | None = None) -> str | None:
    if transcriber is None:
        return None

    return transcriber.transcribe(audio_path)
