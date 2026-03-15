import io
from pathlib import Path
import sys
import wave

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.api.app.models.project import Project
from apps.api.app.models.voice import VoiceSegment
from apps.api.app.services.file_store import FileStore
from apps.cli.app.services.recording import record_voice_segment


class FakeTranscriber:
    def transcribe(self, audio_path: Path) -> str:
        return f"transcript:{audio_path.name}"


def write_wav_file(path: Path, duration_ms: int, sample_rate: int = 8000) -> None:
    frame_count = int(sample_rate * duration_ms / 1000)
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(b"\x00\x00" * frame_count)
    path.write_bytes(buffer.getvalue())


def create_project_with_voice(tmp_path: Path) -> tuple[Path, FileStore]:
    project_dir = tmp_path / "workspace" / "demo-001"
    store = FileStore(project_dir)
    store.save_project(
        Project(
            id="demo-001",
            title="Demo Project",
            sourceLanguage="ja",
            imageDir="images",
            createdAt="2026-03-14T00:00:00Z",
            updatedAt="2026-03-14T00:00:00Z",
        )
    )
    store.save_voices(
        [
            VoiceSegment(
                id="voice-001",
                frameId="frame-001",
                text="Narration voice",
                mode="tts",
                role="narrator",
                speaker="Narrator",
                voicePreset="narrator-default",
                audioFile="audio/narration/original.wav",
                durationMs=300,
            )
        ]
    )
    return project_dir, store


def test_record_voice_segment_creates_audio_artifact_and_links_recording(tmp_path: Path) -> None:
    project_dir, store = create_project_with_voice(tmp_path)
    source_audio = tmp_path / "take-1.wav"
    write_wav_file(source_audio, 450)

    updated_voice = record_voice_segment(
        project_dir,
        "voice-001",
        source_audio_path=source_audio,
        transcriber=FakeTranscriber(),
    )

    assert updated_voice.mode == "record"
    assert updated_voice.audio_file == "audio/recorded/voice-001.wav"
    assert updated_voice.transcript == "transcript:voice-001.wav"
    assert updated_voice.duration_ms == 450
    assert (project_dir / "audio" / "recorded" / "voice-001.wav").read_bytes() == source_audio.read_bytes()

    persisted_voice = store.load_voices()[0]
    assert persisted_voice.mode == "record"
    assert persisted_voice.audio_file == "audio/recorded/voice-001.wav"
    assert persisted_voice.transcript == "transcript:voice-001.wav"
    assert persisted_voice.duration_ms == 450


def test_rerecord_replaces_prior_output_and_skip_allows_later_editing(tmp_path: Path) -> None:
    project_dir, store = create_project_with_voice(tmp_path)

    skipped_voice = record_voice_segment(project_dir, "voice-001", skip=True)
    assert skipped_voice.mode == "skip"
    assert skipped_voice.audio_file is None
    assert skipped_voice.duration_ms is None

    first_take = tmp_path / "take-1.wav"
    second_take = tmp_path / "take-2.wav"
    write_wav_file(first_take, 600)
    write_wav_file(second_take, 900)

    record_voice_segment(project_dir, "voice-001", source_audio_path=first_take)
    updated_voice = record_voice_segment(project_dir, "voice-001", source_audio_path=second_take)

    assert updated_voice.mode == "record"
    assert updated_voice.audio_file == "audio/recorded/voice-001.wav"
    assert updated_voice.duration_ms == 900
    assert (project_dir / "audio" / "recorded" / "voice-001.wav").read_bytes() == second_take.read_bytes()

    persisted_voice = store.load_voices()[0]
    assert persisted_voice.mode == "record"
    assert persisted_voice.audio_file == "audio/recorded/voice-001.wav"
    assert persisted_voice.duration_ms == 900
