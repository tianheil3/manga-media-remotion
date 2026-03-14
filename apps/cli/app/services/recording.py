import shutil
from datetime import datetime, timezone
from pathlib import Path

from apps.api.app.models.voice import VoiceSegment
from apps.api.app.services.file_store import FileStore
from apps.cli.app.services.transcription import Transcriber, transcribe_audio


def record_voice_segment(
    project_dir: Path,
    voice_id: str,
    *,
    source_audio_path: Path | None = None,
    transcriber: Transcriber | None = None,
    skip: bool = False,
) -> VoiceSegment:
    if skip and source_audio_path is not None:
        raise ValueError("Cannot provide source audio when skipping recording.")
    if not skip and source_audio_path is None:
        raise ValueError("A source audio path is required unless the recording is skipped.")

    store = FileStore(project_dir)
    voices = store.load_voices()
    updated_voices: list[VoiceSegment] = []
    matched_voice: VoiceSegment | None = None

    for voice in voices:
        if voice.id != voice_id:
            updated_voices.append(voice)
            continue

        matched_voice = voice
        if skip:
            updated_voices.append(
                voice.model_copy(
                    update={
                        "mode": "skip",
                        "audio_file": None,
                        "transcript": None,
                    }
                )
            )
            continue

        recording_dir = project_dir / "audio" / "recorded"
        recording_dir.mkdir(parents=True, exist_ok=True)
        destination_path = recording_dir / f"{voice.id}.wav"
        shutil.copy2(source_audio_path, destination_path)

        updated_voices.append(
            voice.model_copy(
                update={
                    "mode": "record",
                    "audio_file": str(destination_path.relative_to(project_dir)),
                    "transcript": transcribe_audio(destination_path, transcriber),
                }
            )
        )

    if matched_voice is None:
        raise ValueError(f"Unknown voice segment: {voice_id}")

    store.save_voices(updated_voices)
    project = store.load_project()
    project.updated_at = _utc_timestamp()
    store.save_project(project)
    return next(voice for voice in updated_voices if voice.id == voice_id)


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
