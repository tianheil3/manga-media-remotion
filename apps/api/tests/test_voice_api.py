import json
from pathlib import Path
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.api.app.models.project import Project
from apps.api.app.models.scene import Scene
from apps.api.app.models.voice import VoiceSegment
from apps.api.app.routes.voice import (
    ReplaceAudioRequest,
    SceneUpdate,
    get_scene_review,
    replace_voice_audio,
    skip_voice_recording,
    update_scene,
)
from apps.api.app.services.file_store import FileStore


def create_project_with_scenes(workspace_root: Path, project_id: str) -> Path:
    project_dir = workspace_root / project_id
    store = FileStore(project_dir)
    store.save_project(
        Project(
            id=project_id,
            title=f"Project {project_id}",
            sourceLanguage="ja",
            imageDir="images",
            createdAt="2026-03-14T00:00:00Z",
            updatedAt="2026-03-14T00:00:00Z",
        )
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
            )
        ]
    )
    store.save_scenes(
        [
            Scene(
                id="scene-001",
                type="narration",
                image="images/001.png",
                subtitleText="Original subtitle",
                audio="audio/narration/script-bubble-001.wav",
                durationMs=1400,
                speaker="Narrator",
                stylePreset="default",
                transition="cut",
            )
        ]
    )
    return project_dir


def make_request(workspace_root: Path) -> SimpleNamespace:
    return SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(workspace_root=workspace_root)))


def test_get_scene_review_lists_scenes_with_audio_metadata_and_actions(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    create_project_with_scenes(workspace_root, "demo-001")
    request = make_request(workspace_root)

    assert get_scene_review("demo-001", request) == [
        {
            "id": "scene-001",
            "type": "narration",
            "image": "images/001.png",
            "subtitleText": "Original subtitle",
            "audio": "audio/narration/script-bubble-001.wav",
            "durationMs": 1400,
            "speaker": "Narrator",
            "stylePreset": "default",
            "cameraMotion": None,
            "transition": "cut",
            "audioMetadata": {
                "id": "voice-script-bubble-001",
                "frameId": "frame-001",
                "mode": "tts",
                "role": "narrator",
                "speaker": "Narrator",
                "audioFile": "audio/narration/script-bubble-001.wav",
                "durationMs": 1200,
                "replaceAudioPath": "/projects/demo-001/voices/voice-script-bubble-001/audio",
                "skipRecordingPath": "/projects/demo-001/voices/voice-script-bubble-001/skip",
            },
        }
    ]


def test_update_scene_persists_subtitle_duration_and_style(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    project_dir = create_project_with_scenes(workspace_root, "demo-001")
    request = make_request(workspace_root)

    updated_scene = update_scene(
        "demo-001",
        "scene-001",
        SceneUpdate(
            subtitleText="Edited subtitle",
            durationMs=1800,
            stylePreset="dramatic",
        ),
        request,
    )

    assert updated_scene == {
        "id": "scene-001",
        "type": "narration",
        "image": "images/001.png",
        "subtitleText": "Edited subtitle",
        "audio": "audio/narration/script-bubble-001.wav",
        "durationMs": 1800,
        "speaker": "Narrator",
        "stylePreset": "dramatic",
        "cameraMotion": None,
        "transition": "cut",
    }

    stored_scenes = json.loads((project_dir / "script" / "scenes.json").read_text(encoding="utf-8"))
    assert stored_scenes == [updated_scene]


def test_replace_voice_audio_updates_the_voice_segment(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    project_dir = create_project_with_scenes(workspace_root, "demo-001")
    request = make_request(workspace_root)
    source_audio = tmp_path / "replacement.wav"
    source_audio.write_bytes(b"replacement audio")

    updated_voice = replace_voice_audio(
        "demo-001",
        "voice-script-bubble-001",
        ReplaceAudioRequest(sourceAudioPath=str(source_audio)),
        request,
    )

    assert updated_voice == {
        "id": "voice-script-bubble-001",
        "frameId": "frame-001",
        "text": "Narration voice",
        "mode": "record",
        "role": "narrator",
        "speaker": "Narrator",
        "voicePreset": "narrator-default",
        "audioFile": "audio/recorded/voice-script-bubble-001.wav",
        "transcript": None,
        "durationMs": 1200,
    }
    assert (project_dir / "audio" / "recorded" / "voice-script-bubble-001.wav").read_bytes() == b"replacement audio"


def test_skip_voice_recording_marks_the_segment_as_skipped(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    create_project_with_scenes(workspace_root, "demo-001")
    request = make_request(workspace_root)

    updated_voice = skip_voice_recording("demo-001", "voice-script-bubble-001", request)

    assert updated_voice == {
        "id": "voice-script-bubble-001",
        "frameId": "frame-001",
        "text": "Narration voice",
        "mode": "skip",
        "role": "narrator",
        "speaker": "Narrator",
        "voicePreset": "narrator-default",
        "audioFile": None,
        "transcript": None,
        "durationMs": 1200,
    }
