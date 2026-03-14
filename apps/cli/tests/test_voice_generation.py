import json
from pathlib import Path
import sys

from typer.testing import CliRunner

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.api.app.models.project import Project
from apps.api.app.services.file_store import FileStore
from apps.cli.app.main import app
import apps.cli.app.services.voice_generation as voice_generation

runner = CliRunner()


class FakeTtsProvider:
    def synthesize(self, text: str, voice_preset: str) -> bytes:
        return f"{voice_preset}:{text}".encode("utf-8")


class FailingTtsProvider:
    def synthesize(self, text: str, voice_preset: str) -> bytes:
        raise RuntimeError("provider exploded")


def create_project_with_script(tmp_path: Path) -> tuple[Path, Path]:
    workspace_root = tmp_path / "workspace"
    project_dir = workspace_root / "demo-001"
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
    (project_dir / "script").mkdir(parents=True, exist_ok=True)
    (project_dir / "script" / "script.json").write_text(
        json.dumps(
            [
                {
                    "id": "script-bubble-001",
                    "frameId": "frame-001",
                    "sourceBubbleId": "bubble-001",
                    "sourceText": "Narration source",
                    "translatedText": "Narration translation",
                    "voiceText": "Narration voice",
                    "subtitleText": "Narration subtitle",
                    "kind": "narration",
                    "speaker": "Narrator",
                },
                {
                    "id": "script-bubble-002",
                    "frameId": "frame-002",
                    "sourceBubbleId": "bubble-002",
                    "sourceText": "Dialogue source",
                    "translatedText": "Dialogue translation",
                    "voiceText": "Dialogue voice",
                    "subtitleText": "Dialogue subtitle",
                    "kind": "dialogue",
                    "speaker": "Hero",
                },
            ]
        ),
        encoding="utf-8",
    )

    return workspace_root, project_dir


def test_voice_command_persists_audio_paths_and_voice_presets(
    tmp_path: Path,
    monkeypatch,
) -> None:
    workspace_root, project_dir = create_project_with_script(tmp_path)
    monkeypatch.setattr(voice_generation, "get_tts_provider", lambda: FakeTtsProvider())

    result = runner.invoke(
        app,
        ["voice", "demo-001", "--workspace-root", str(workspace_root)],
    )

    assert result.exit_code == 0, result.stdout

    voices_payload = json.loads((project_dir / "script" / "voices.json").read_text(encoding="utf-8"))
    assert voices_payload == [
        {
            "id": "voice-script-bubble-001",
            "frameId": "frame-001",
            "text": "Narration voice",
            "mode": "tts",
            "role": "narrator",
            "speaker": "Narrator",
            "voicePreset": "narrator-default",
            "audioFile": "audio/narration/script-bubble-001.wav",
            "transcript": None,
            "durationMs": None,
        },
        {
            "id": "voice-script-bubble-002",
            "frameId": "frame-002",
            "text": "Dialogue voice",
            "mode": "tts",
            "role": "character",
            "speaker": "Hero",
            "voicePreset": "character-default",
            "audioFile": "audio/characters/script-bubble-002.wav",
            "transcript": None,
            "durationMs": None,
        },
    ]

    assert (project_dir / "audio" / "narration" / "script-bubble-001.wav").read_bytes() == (
        b"narrator-default:Narration voice"
    )
    assert (project_dir / "audio" / "characters" / "script-bubble-002.wav").read_bytes() == (
        b"character-default:Dialogue voice"
    )


def test_voice_command_surfaces_provider_errors(tmp_path: Path, monkeypatch) -> None:
    workspace_root, _project_dir = create_project_with_script(tmp_path)
    monkeypatch.setattr(voice_generation, "get_tts_provider", lambda: FailingTtsProvider())

    result = runner.invoke(
        app,
        ["voice", "demo-001", "--workspace-root", str(workspace_root)],
    )

    assert result.exit_code == 1, result.stdout
    assert "TTS generation failed for script-bubble-001: provider exploded" in result.stdout
