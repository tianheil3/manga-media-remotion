import json
from pathlib import Path
import sys

from typer.testing import CliRunner

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.api.app.models.frame import Frame, ReviewedBubble
from apps.api.app.models.project import Project
from apps.api.app.models.voice import VoiceSegment
from apps.api.app.services.file_store import FileStore
from apps.cli.app.main import app

runner = CliRunner()


def create_project_for_scene_builder(tmp_path: Path) -> tuple[Path, Path]:
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
    store.save_frames(
        [
            Frame(
                frameId="frame-001",
                image="images/001.png",
                ocrFile="ocr/001.json",
                reviewedBubbles=[
                    ReviewedBubble(
                        id="review-bubble-001",
                        sourceBubbleId="bubble-001",
                        textOriginal="original-1",
                        textEdited="edited-1",
                        order=0,
                        kind="narration",
                    )
                ],
            ),
            Frame(
                frameId="frame-002",
                image="images/002.png",
                ocrFile="ocr/002.json",
                reviewedBubbles=[],
            ),
            Frame(
                frameId="frame-003",
                image="images/003.png",
                ocrFile="ocr/003.json",
                reviewedBubbles=[
                    ReviewedBubble(
                        id="review-bubble-003",
                        sourceBubbleId="bubble-003",
                        textOriginal="original-3",
                        textEdited="edited-3",
                        order=0,
                        kind="dialogue",
                        speaker="Hero",
                    )
                ],
            ),
        ]
    )
    store.save_voices(
        [
            VoiceSegment(
                id="voice-script-bubble-001",
                frameId="frame-001",
                text="Narration voice",
                mode="tts",
                role="narrator",
                speaker="Narrator",
                voicePreset="narrator-default",
                audioFile="audio/narration/script-bubble-001.wav",
                durationMs=1200,
            ),
            VoiceSegment(
                id="voice-script-bubble-003",
                frameId="frame-003",
                text="Dialogue voice",
                mode="tts",
                role="character",
                speaker="Hero",
                voicePreset="character-default",
                audioFile="audio/characters/script-bubble-003.wav",
                durationMs=800,
            ),
        ]
    )
    (project_dir / "script" / "script.json").write_text(
        json.dumps(
            [
                {
                    "id": "script-bubble-001",
                    "frameId": "frame-001",
                    "sourceBubbleId": "bubble-001",
                    "sourceText": "edited-1",
                    "translatedText": "translated-1",
                    "voiceText": "Narration voice",
                    "subtitleText": "Narration subtitle",
                    "kind": "narration",
                    "speaker": "Narrator",
                },
                {
                    "id": "script-bubble-003",
                    "frameId": "frame-003",
                    "sourceBubbleId": "bubble-003",
                    "sourceText": "edited-3",
                    "translatedText": "translated-3",
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


def test_build_scenes_creates_render_ready_order_with_audio_padding_and_silent_frames(
    tmp_path: Path,
) -> None:
    workspace_root, project_dir = create_project_for_scene_builder(tmp_path)

    result = runner.invoke(
        app,
        [
            "build-scenes",
            "demo-001",
            "--padding-ms",
            "200",
            "--silent-duration-ms",
            "1500",
            "--workspace-root",
            str(workspace_root),
        ],
    )

    assert result.exit_code == 0, result.stdout

    scenes_payload = json.loads((project_dir / "script" / "scenes.json").read_text(encoding="utf-8"))
    assert scenes_payload == [
        {
            "id": "scene-001",
            "type": "narration",
            "image": "images/001.png",
            "subtitleText": "Narration subtitle",
            "audio": "audio/narration/script-bubble-001.wav",
            "durationMs": 1400,
            "speaker": "Narrator",
            "stylePreset": "default",
            "cameraMotion": None,
            "transition": "cut",
        },
        {
            "id": "scene-002",
            "type": "silent",
            "image": "images/002.png",
            "subtitleText": None,
            "audio": None,
            "durationMs": 1500,
            "speaker": None,
            "stylePreset": "default",
            "cameraMotion": None,
            "transition": "cut",
        },
        {
            "id": "scene-003",
            "type": "dialogue",
            "image": "images/003.png",
            "subtitleText": "Dialogue subtitle",
            "audio": "audio/characters/script-bubble-003.wav",
            "durationMs": 1000,
            "speaker": "Hero",
            "stylePreset": "default",
            "cameraMotion": None,
            "transition": "cut",
        },
    ]


def test_build_scenes_requires_voice_generation_before_creating_scenes(tmp_path: Path) -> None:
    workspace_root, project_dir = create_project_for_scene_builder(tmp_path)
    (project_dir / "script" / "voices.json").unlink()

    result = runner.invoke(
        app,
        [
            "build-scenes",
            "demo-001",
            "--workspace-root",
            str(workspace_root),
        ],
    )

    assert result.exit_code == 1
    assert "No voice segments found. Run voice before building scenes." in result.stdout


def test_build_scenes_requires_imported_frames_before_creating_scenes(tmp_path: Path) -> None:
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

    result = runner.invoke(
        app,
        [
            "build-scenes",
            "demo-001",
            "--workspace-root",
            str(workspace_root),
        ],
    )

    assert result.exit_code == 1
    assert "No frames found. Import images before building scenes." in result.stdout


def test_build_scenes_falls_back_to_voice_text_when_script_file_is_missing(tmp_path: Path) -> None:
    workspace_root, project_dir = create_project_for_scene_builder(tmp_path)
    (project_dir / "script" / "script.json").unlink()

    result = runner.invoke(
        app,
        [
            "build-scenes",
            "demo-001",
            "--workspace-root",
            str(workspace_root),
        ],
    )

    assert result.exit_code == 0, result.stdout

    scenes_payload = json.loads((project_dir / "script" / "scenes.json").read_text(encoding="utf-8"))
    assert scenes_payload == [
        {
            "id": "scene-001",
            "type": "narration",
            "image": "images/001.png",
            "subtitleText": "Narration voice",
            "audio": "audio/narration/script-bubble-001.wav",
            "durationMs": 1400,
            "speaker": "Narrator",
            "stylePreset": "default",
            "cameraMotion": None,
            "transition": "cut",
        },
        {
            "id": "scene-002",
            "type": "silent",
            "image": "images/002.png",
            "subtitleText": None,
            "audio": None,
            "durationMs": 1500,
            "speaker": None,
            "stylePreset": "default",
            "cameraMotion": None,
            "transition": "cut",
        },
        {
            "id": "scene-003",
            "type": "dialogue",
            "image": "images/003.png",
            "subtitleText": "Dialogue voice",
            "audio": "audio/characters/script-bubble-003.wav",
            "durationMs": 1000,
            "speaker": "Hero",
            "stylePreset": "default",
            "cameraMotion": None,
            "transition": "cut",
        },
    ]
