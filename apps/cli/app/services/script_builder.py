import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from apps.api.app.models.frame import Frame
from apps.api.app.models.project import Project
from apps.api.app.services.file_store import FileStore
from apps.cli.app.services.translation_service import TranslationService


class ScriptOverride(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    source_bubble_id: str = Field(alias="sourceBubbleId")
    translated_text: str | None = Field(default=None, alias="translatedText")
    voice_text: str | None = Field(default=None, alias="voiceText")
    subtitle_text: str | None = Field(default=None, alias="subtitleText")


class ScriptEntry(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    frame_id: str = Field(alias="frameId")
    source_bubble_id: str = Field(alias="sourceBubbleId")
    source_text: str = Field(alias="sourceText")
    translated_text: str = Field(alias="translatedText")
    voice_text: str = Field(alias="voiceText")
    subtitle_text: str = Field(alias="subtitleText")
    kind: Literal["dialogue", "narration", "sfx", "ignore"]
    speaker: str | None = None


def load_script_overrides(overrides_file: Path | None) -> dict[str, ScriptOverride]:
    if overrides_file is None:
        return {}

    payload = json.loads(overrides_file.read_text(encoding="utf-8"))
    overrides = [ScriptOverride.model_validate(item) for item in payload]
    return {override.source_bubble_id: override for override in overrides}


def build_script_entries(
    frames: list[Frame],
    *,
    translation_service: TranslationService,
    source_language: str,
    target_language: str,
    overrides: dict[str, ScriptOverride] | None = None,
) -> list[ScriptEntry]:
    entries: list[ScriptEntry] = []
    resolved_overrides = overrides or {}

    for frame in frames:
        for reviewed_bubble in frame.reviewed_bubbles:
            if reviewed_bubble.kind == "ignore":
                continue

            translated_text = translation_service.translate_text(
                reviewed_bubble.text_edited,
                source_language,
                target_language,
            )
            override = resolved_overrides.get(reviewed_bubble.source_bubble_id)
            if override and override.translated_text is not None:
                translated_text = override.translated_text

            voice_text = translated_text
            if override and override.voice_text is not None:
                voice_text = override.voice_text

            subtitle_text = voice_text
            if override and override.subtitle_text is not None:
                subtitle_text = override.subtitle_text

            entries.append(
                ScriptEntry(
                    id=f"script-{reviewed_bubble.source_bubble_id}",
                    frameId=frame.frame_id,
                    sourceBubbleId=reviewed_bubble.source_bubble_id,
                    sourceText=reviewed_bubble.text_edited,
                    translatedText=translated_text,
                    voiceText=voice_text,
                    subtitleText=subtitle_text,
                    kind=reviewed_bubble.kind,
                    speaker=reviewed_bubble.speaker,
                )
            )

    return entries


def save_script_entries(project_dir: Path, entries: list[ScriptEntry]) -> None:
    script_path = project_dir / "script" / "script.json"
    script_path.parent.mkdir(parents=True, exist_ok=True)
    script_path.write_text(
        json.dumps([entry.model_dump(mode="json", by_alias=True) for entry in entries], indent=2) + "\n",
        encoding="utf-8",
    )


def load_script_entries(project_dir: Path) -> list[ScriptEntry]:
    script_path = project_dir / "script" / "script.json"
    payload = json.loads(script_path.read_text(encoding="utf-8"))
    return [ScriptEntry.model_validate(item) for item in payload]


def run_translation(
    project_dir: Path,
    *,
    project: Project,
    translation_service: TranslationService,
    target_language: str,
    overrides: dict[str, ScriptOverride] | None = None,
) -> list[ScriptEntry]:
    frames = FileStore(project_dir).load_frames()
    if not any(frame.reviewed_bubbles for frame in frames):
        raise ValueError("No reviewed text found. Run review before translation.")

    entries = build_script_entries(
        frames,
        translation_service=translation_service,
        source_language=project.source_language,
        target_language=target_language,
        overrides=overrides,
    )
    save_script_entries(project_dir, entries)

    store = FileStore(project_dir)
    refreshed_project = store.load_project()
    refreshed_project.updated_at = _utc_timestamp()
    store.save_project(refreshed_project)
    return entries


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
