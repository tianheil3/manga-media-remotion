from datetime import datetime, timezone
from pathlib import Path

from apps.api.app.models.scene import Scene
from apps.api.app.models.voice import VoiceSegment
from apps.api.app.services.file_store import FileStore
from apps.cli.app.services.scene_sync import resolve_voice_duration_ms
from apps.cli.app.services.script_builder import load_script_entries


def build_scenes(
    project_dir: Path,
    *,
    padding_ms: int = 200,
    silent_duration_ms: int = 1500,
) -> list[Scene]:
    store = FileStore(project_dir)
    frames = _load_optional_list(store.load_frames)

    if not frames:
        raise ValueError("No frames found. Import images before building scenes.")

    voices = _load_optional_list(store.load_voices)
    if not voices:
        raise ValueError("No voice segments found. Run voice before building scenes.")

    script_entries = {entry.id: entry for entry in _load_optional_script_entries(project_dir)}

    scenes: list[Scene] = []
    for frame in frames:
        frame_voices = [voice for voice in voices if voice.frame_id == frame.frame_id]
        if not frame_voices:
            scenes.append(
                Scene(
                    id=f"scene-{len(scenes) + 1:03d}",
                    type="silent",
                    image=frame.image,
                    subtitleText=None,
                    voiceId=None,
                    audio=None,
                    durationMs=silent_duration_ms,
                    speaker=None,
                    stylePreset="default",
                    cameraMotion=None,
                    transition="cut",
                )
            )
            continue

        for voice in frame_voices:
            script_entry = script_entries.get(voice.id.removeprefix("voice-"))
            subtitle_text = script_entry.subtitle_text if script_entry else voice.text
            scene_type = "narration" if voice.role == "narrator" else "dialogue"
            duration_ms = _scene_duration_ms(project_dir, voice, padding_ms, silent_duration_ms)
            scenes.append(
                Scene(
                    id=f"scene-{len(scenes) + 1:03d}",
                    type=scene_type,
                    image=frame.image,
                    subtitleText=subtitle_text,
                    voiceId=voice.id,
                    audio=voice.audio_file,
                    durationMs=duration_ms,
                    speaker=voice.speaker,
                    stylePreset="default",
                    cameraMotion=None,
                    transition="cut",
                )
            )

    store.save_scenes(scenes)
    project = store.load_project()
    project.updated_at = _utc_timestamp()
    store.save_project(project)
    return scenes


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_optional_list(loader):
    try:
        return loader()
    except FileNotFoundError:
        return []


def _load_optional_script_entries(project_dir: Path):
    try:
        return load_script_entries(project_dir)
    except FileNotFoundError:
        return []


def _scene_duration_ms(
    project_dir: Path,
    voice: VoiceSegment,
    padding_ms: int,
    silent_duration_ms: int,
) -> int:
    duration_ms = resolve_voice_duration_ms(project_dir, voice)
    if voice.audio_file is None or duration_ms is None:
        return silent_duration_ms
    return duration_ms + padding_ms
