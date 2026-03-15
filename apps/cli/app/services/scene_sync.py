from pathlib import Path

from apps.api.app.models.scene import Scene
from apps.api.app.models.voice import VoiceSegment
from apps.api.app.services.file_store import FileStore
from apps.cli.app.services.audio_duration import measure_wav_duration_ms

DEFAULT_PADDING_MS = 200
DEFAULT_SILENT_DURATION_MS = 1500


def resolve_voice_duration_ms(project_dir: Path, voice: VoiceSegment) -> int | None:
    if voice.duration_ms is not None:
        return voice.duration_ms
    if voice.audio_file is None:
        return None
    return measure_wav_duration_ms(project_dir / voice.audio_file)


def resolve_voice_for_scene(scene: Scene, voices: list[VoiceSegment]) -> VoiceSegment | None:
    voices_by_id = {voice.id: voice for voice in voices}
    if scene.voice_id is not None:
        return voices_by_id.get(scene.voice_id)
    if scene.audio is None:
        return None
    return next((voice for voice in voices if voice.audio_file == scene.audio), None)


def resolve_scene_voice_ids(
    scenes: list[Scene],
    voices: list[VoiceSegment],
    *,
    previous_voices: list[VoiceSegment] | None = None,
) -> dict[str, str]:
    prior_voices = previous_voices or voices
    previous_audio_ids = {voice.audio_file: voice.id for voice in prior_voices if voice.audio_file}
    current_audio_ids = {voice.audio_file: voice.id for voice in voices if voice.audio_file}
    return _resolve_scene_voice_ids(
        scenes,
        voices,
        previous_audio_ids=previous_audio_ids,
        current_audio_ids=current_audio_ids,
    )


def sync_scenes_with_updated_voices(
    project_dir: Path,
    previous_voices: list[VoiceSegment],
    current_voices: list[VoiceSegment],
    *,
    default_padding_ms: int = DEFAULT_PADDING_MS,
    default_silent_duration_ms: int = DEFAULT_SILENT_DURATION_MS,
) -> list[Scene]:
    store = FileStore(project_dir)
    try:
        scenes = store.load_scenes()
    except FileNotFoundError:
        return []

    previous_by_id = {voice.id: voice for voice in previous_voices}
    current_by_id = {voice.id: voice for voice in current_voices}
    scene_voice_ids = resolve_scene_voice_ids(
        scenes,
        current_voices,
        previous_voices=previous_voices,
    )

    updated_scenes: list[Scene] = []
    changed = False
    for scene in scenes:
        voice_id = scene_voice_ids.get(scene.id)

        if voice_id is None:
            updated_scenes.append(scene)
            continue

        current_voice = current_by_id.get(voice_id)
        if current_voice is None:
            updated_scenes.append(scene)
            continue

        previous_voice = previous_by_id.get(voice_id, current_voice)
        updated_scene = scene.model_copy(
            update={
                "voice_id": voice_id,
                "audio": current_voice.audio_file,
                "duration_ms": _scene_duration_ms(
                    project_dir,
                    scene,
                    previous_voice,
                    current_voice,
                    default_padding_ms=default_padding_ms,
                    default_silent_duration_ms=default_silent_duration_ms,
                ),
                "speaker": current_voice.speaker,
            }
        )
        updated_scenes.append(updated_scene)
        changed = changed or updated_scene != scene

    if changed:
        store.save_scenes(updated_scenes)

    return updated_scenes


def _resolve_scene_voice_ids(
    scenes: list[Scene],
    voices: list[VoiceSegment],
    *,
    previous_audio_ids: dict[str, str],
    current_audio_ids: dict[str, str],
) -> dict[str, str]:
    scene_voice_ids: dict[str, str] = {}
    assigned_voice_ids: set[str] = set()

    for scene in scenes:
        voice_id = scene.voice_id
        if voice_id is None and scene.audio is not None:
            voice_id = previous_audio_ids.get(scene.audio) or current_audio_ids.get(scene.audio)
        if voice_id is None:
            continue
        scene_voice_ids[scene.id] = voice_id
        assigned_voice_ids.add(voice_id)

    remaining_voice_ids = [voice.id for voice in voices if voice.id not in assigned_voice_ids]
    remaining_voice_iter = iter(remaining_voice_ids)
    for scene in scenes:
        if scene.id in scene_voice_ids or scene.type == "silent":
            continue
        voice_id = next(remaining_voice_iter, None)
        if voice_id is None:
            break
        scene_voice_ids[scene.id] = voice_id

    return scene_voice_ids


def _scene_duration_ms(
    project_dir: Path,
    scene: Scene,
    previous_voice: VoiceSegment,
    current_voice: VoiceSegment,
    *,
    default_padding_ms: int,
    default_silent_duration_ms: int,
) -> int:
    current_duration_ms = resolve_voice_duration_ms(project_dir, current_voice)
    if current_voice.audio_file is None or current_duration_ms is None:
        return default_silent_duration_ms

    padding_ms = _scene_padding_ms(project_dir, scene, previous_voice, default_padding_ms)
    return current_duration_ms + padding_ms


def _scene_padding_ms(
    project_dir: Path,
    scene: Scene,
    previous_voice: VoiceSegment,
    default_padding_ms: int,
) -> int:
    previous_duration_ms = resolve_voice_duration_ms(project_dir, previous_voice)
    if previous_duration_ms is None:
        return default_padding_ms

    return max(scene.duration_ms - previous_duration_ms, 0)
