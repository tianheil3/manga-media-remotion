from pathlib import Path
import sys

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
            )
        ]
    )
    return project_dir, store


def test_record_voice_segment_creates_audio_artifact_and_links_recording(tmp_path: Path) -> None:
    project_dir, store = create_project_with_voice(tmp_path)
    source_audio = tmp_path / "take-1.wav"
    source_audio.write_bytes(b"first take")

    updated_voice = record_voice_segment(
        project_dir,
        "voice-001",
        source_audio_path=source_audio,
        transcriber=FakeTranscriber(),
    )

    assert updated_voice.mode == "record"
    assert updated_voice.audio_file == "audio/recorded/voice-001.wav"
    assert updated_voice.transcript == "transcript:voice-001.wav"
    assert (project_dir / "audio" / "recorded" / "voice-001.wav").read_bytes() == b"first take"

    persisted_voice = store.load_voices()[0]
    assert persisted_voice.mode == "record"
    assert persisted_voice.audio_file == "audio/recorded/voice-001.wav"
    assert persisted_voice.transcript == "transcript:voice-001.wav"


def test_rerecord_replaces_prior_output_and_skip_allows_later_editing(tmp_path: Path) -> None:
    project_dir, store = create_project_with_voice(tmp_path)

    skipped_voice = record_voice_segment(project_dir, "voice-001", skip=True)
    assert skipped_voice.mode == "skip"
    assert skipped_voice.audio_file is None

    first_take = tmp_path / "take-1.wav"
    second_take = tmp_path / "take-2.wav"
    first_take.write_bytes(b"first take")
    second_take.write_bytes(b"second take")

    record_voice_segment(project_dir, "voice-001", source_audio_path=first_take)
    updated_voice = record_voice_segment(project_dir, "voice-001", source_audio_path=second_take)

    assert updated_voice.mode == "record"
    assert updated_voice.audio_file == "audio/recorded/voice-001.wav"
    assert (project_dir / "audio" / "recorded" / "voice-001.wav").read_bytes() == b"second take"

    persisted_voice = store.load_voices()[0]
    assert persisted_voice.mode == "record"
    assert persisted_voice.audio_file == "audio/recorded/voice-001.wav"
