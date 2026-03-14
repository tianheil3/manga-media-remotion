from pathlib import Path
from typing import Protocol


class TranslationService(Protocol):
    def translate_text(self, text: str, source_language: str, target_language: str) -> str:
        ...


class PassthroughTranslationService:
    def translate_text(self, text: str, source_language: str, target_language: str) -> str:
        return text


def get_translation_service() -> TranslationService:
    return PassthroughTranslationService()
