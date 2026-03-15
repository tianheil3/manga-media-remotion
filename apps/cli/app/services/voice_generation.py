from datetime import datetime, timezone
from pathlib import Path

from apps.api.app.integrations.moyin_tts import MoyinTtsClient
from apps.api.app.models.voice import VoiceSegment
from apps.api.app.services.file_store import FileStore
from apps.cli.app.services.audio_duration import measure_wav_duration_ms
from apps.cli.app.services.script_builder import load_script_entries


def get_tts_provider() -> MoyinTtsClient:
    return MoyinTtsClient.from_env()


def generate_voices(project_dir: Path, provider=None) -> list[VoiceSegment]:
    script_entries = load_script_entries(project_dir)
    if not script_entries:
        raise ValueError("No script entries found. Run translate before voice generation.")

    tts_provider = provider or get_tts_provider()
    voices: list[VoiceSegment] = []

    for entry in script_entries:
        role, voice_preset, folder = _voice_config(entry.kind)
        try:
            audio_bytes = tts_provider.synthesize(entry.voice_text, voice_preset)
        except Exception as exc:
            raise ValueError(f"TTS generation failed for {entry.id}: {exc}") from exc

        audio_dir = project_dir / "audio" / folder
        audio_dir.mkdir(parents=True, exist_ok=True)
        audio_path = audio_dir / f"{entry.id}.wav"
        audio_path.write_bytes(audio_bytes)
        duration_ms = measure_wav_duration_ms(audio_path)

        voices.append(
            VoiceSegment(
                id=f"voice-{entry.id}",
                frameId=entry.frame_id,
                text=entry.voice_text,
                mode="tts",
                role=role,
                speaker=entry.speaker,
                voicePreset=voice_preset,
                audioFile=str(audio_path.relative_to(project_dir)),
                durationMs=duration_ms,
            )
        )

    store = FileStore(project_dir)
    store.save_voices(voices)
    project = store.load_project()
    project.updated_at = _utc_timestamp()
    store.save_project(project)
    return voices


def _voice_config(kind: str) -> tuple[str, str, str]:
    if kind == "narration":
        return ("narrator", "narrator-default", "narration")

    return ("character", "character-default", "characters")


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
