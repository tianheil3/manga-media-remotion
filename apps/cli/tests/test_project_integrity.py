import json
from pathlib import Path
import sys

from typer.testing import CliRunner

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.api.app.models.frame import Frame
from apps.api.app.models.project import Project
from apps.api.app.models.scene import Scene
from apps.api.app.models.voice import VoiceSegment
from apps.api.app.services.file_store import FileStore
from apps.cli.app.main import app

runner = CliRunner()


def write_project(project_dir: Path, *, write_config: bool = True) -> FileStore:
    store = FileStore(project_dir)
    store.save_project(
        Project(
            id=project_dir.name,
            title=f"Project {project_dir.name}",
            sourceLanguage="ja",
            imageDir="images",
            createdAt="2026-03-16T00:00:00Z",
            updatedAt="2026-03-16T00:00:00Z",
        )
    )
    if write_config:
        (project_dir / "config.json").write_text(
            json.dumps({"projectId": project_dir.name}, indent=2) + "\n",
            encoding="utf-8",
        )
    return store


def write_frame_media(project_dir: Path) -> None:
    (project_dir / "images" / "001.png").parent.mkdir(parents=True, exist_ok=True)
    (project_dir / "images" / "001.png").write_bytes(b"png")
    (project_dir / "ocr" / "001.json").parent.mkdir(parents=True, exist_ok=True)
    (project_dir / "ocr" / "001.json").write_text("[]\n", encoding="utf-8")


def write_voice_media(project_dir: Path, relative_path: str = "audio/characters/voice-001.wav") -> None:
    media_path = project_dir / relative_path
    media_path.parent.mkdir(parents=True, exist_ok=True)
    media_path.write_bytes(b"wav")


def create_frame() -> Frame:
    return Frame(
        frameId="frame-001",
        image="images/001.png",
        ocrFile="ocr/001.json",
        bubbles=[],
        reviewedBubbles=[],
    )


def create_voice(*, audio_file: str = "audio/characters/voice-001.wav") -> VoiceSegment:
    return VoiceSegment(
        id="voice-001",
        frameId="frame-001",
        text="voice line",
        mode="tts",
        role="character",
        speaker="Hero",
        voicePreset="character-default",
        audioFile=audio_file,
        durationMs=900,
    )


def create_scene(
    *,
    voice_id: str | None = "voice-001",
    audio: str | None = "audio/characters/voice-001.wav",
    speaker: str | None = "Hero",
) -> Scene:
    return Scene(
        id="scene-001",
        type="dialogue",
        image="images/001.png",
        subtitleText="Subtitle",
        voiceId=voice_id,
        audio=audio,
        durationMs=1100,
        speaker=speaker,
        stylePreset="default",
        transition="cut",
    )


def test_integrity_command_reports_missing_files_media_and_broken_references(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    project_dir = workspace_root / "demo-001"
    store = write_project(project_dir, write_config=False)
    store.save_frames([create_frame()])
    store.save_voices([create_voice()])
    store.save_scenes(
        [
            create_scene(
                voice_id="voice-missing",
                audio="audio/characters/stale.wav",
                speaker="Stale",
            )
        ]
    )

    result = runner.invoke(
        app,
        ["integrity", "demo-001", "--workspace-root", str(workspace_root)],
    )

    assert result.exit_code == 1, result.stdout
    assert "Missing project file: config.json" in result.stdout
    assert "Missing media file: images/001.png" in result.stdout
    assert "Broken scene/voice reference: scene-001" in result.stdout
    assert "repair demo-001" in result.stdout


def test_repair_command_recreates_missing_config_and_script_files(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    project_dir = workspace_root / "demo-001"
    store = write_project(project_dir, write_config=False)
    store.save_frames([create_frame()])
    write_frame_media(project_dir)
    (project_dir / "script" / "voices.json").unlink(missing_ok=True)
    (project_dir / "script" / "scenes.json").unlink(missing_ok=True)

    result = runner.invoke(
        app,
        ["repair", "demo-001", "--workspace-root", str(workspace_root)],
    )

    assert result.exit_code == 0, result.stdout
    assert json.loads((project_dir / "config.json").read_text(encoding="utf-8")) == {"projectId": "demo-001"}
    assert json.loads((project_dir / "script" / "voices.json").read_text(encoding="utf-8")) == []
    assert json.loads((project_dir / "script" / "scenes.json").read_text(encoding="utf-8")) == []
    assert "Project integrity OK" in result.stdout


def test_repair_command_resyncs_stale_scene_links(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    project_dir = workspace_root / "demo-001"
    store = write_project(project_dir)
    store.save_frames([create_frame()])
    store.save_voices([create_voice()])
    store.save_scenes(
        [
            create_scene(
                voice_id="voice-missing",
                audio="audio/characters/stale.wav",
                speaker="Stale",
            )
        ]
    )
    write_frame_media(project_dir)
    write_voice_media(project_dir)

    result = runner.invoke(
        app,
        ["repair", "demo-001", "--workspace-root", str(workspace_root)],
    )

    assert result.exit_code == 0, result.stdout
    repaired_scenes = json.loads((project_dir / "script" / "scenes.json").read_text(encoding="utf-8"))
    assert repaired_scenes[0]["voiceId"] == "voice-001"
    assert repaired_scenes[0]["audio"] == "audio/characters/voice-001.wav"
    assert repaired_scenes[0]["speaker"] == "Hero"
    assert "Resynced scene voice links." in result.stdout


def test_run_command_surfaces_actionable_integrity_errors_for_missing_files(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    project_dir = workspace_root / "demo-001"
    store = write_project(project_dir)
    store.save_frames([create_frame()])
    (project_dir / "script" / "voices.json").unlink(missing_ok=True)

    result = runner.invoke(
        app,
        ["run", "demo-001", "--workspace-root", str(workspace_root)],
    )

    assert result.exit_code == 1, result.stdout
    assert "Project integrity check failed" in result.stdout
    assert "Missing project file: script/voices.json" in result.stdout
    assert "repair demo-001" in result.stdout
