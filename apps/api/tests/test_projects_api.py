from pathlib import Path
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.api.app.models.frame import Frame, OcrBubble, ReviewedBubble
from apps.api.app.models.project import Project
from apps.api.app.models.scene import Scene
from apps.api.app.models.voice import VoiceSegment
from apps.api.app.routes.projects import get_project, list_projects
from apps.api.app.routes.scenes import get_scenes
from apps.api.app.services.file_store import FileStore


def create_project(
    workspace_root: Path,
    project_id: str,
    *,
    complete: bool,
) -> None:
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

    frames = [
        Frame(
            frameId="frame-001",
            image="images/001.png",
            ocrFile="ocr/001.json",
            bubbles=[
                OcrBubble(
                    id="bubble-001",
                    text="raw",
                    bbox={"x": 1, "y": 1, "w": 10, "h": 10},
                    order=0,
                    confidence=0.9,
                    language="ja",
                )
            ],
            reviewedBubbles=[
                ReviewedBubble(
                    id="review-bubble-001",
                    sourceBubbleId="bubble-001",
                    textOriginal="raw",
                    textEdited="edited",
                    order=0,
                    kind="dialogue",
                    speaker="Hero",
                )
            ]
            if complete
            else [],
        )
    ]
    store.save_frames(frames)

    if complete:
        store.save_voices(
            [
                VoiceSegment(
                    id="voice-script-bubble-001",
                    frameId="frame-001",
                    text="voice line",
                    mode="tts",
                    role="character",
                    speaker="Hero",
                    voicePreset="character-default",
                    audioFile="audio/characters/script-bubble-001.wav",
                    durationMs=900,
                )
            ]
        )
        store.save_scenes(
            [
                Scene(
                    id="scene-001",
                    type="dialogue",
                    image="images/001.png",
                    subtitleText="subtitle",
                    audio="audio/characters/script-bubble-001.wav",
                    durationMs=1100,
                    speaker="Hero",
                    stylePreset="default",
                    transition="cut",
                )
            ]
        )
        (project_dir / "script" / "script.json").write_text(
            """[
  {
    "id": "script-bubble-001",
    "frameId": "frame-001",
    "sourceBubbleId": "bubble-001",
    "sourceText": "edited",
    "translatedText": "translated",
    "voiceText": "voice line",
    "subtitleText": "subtitle",
    "kind": "dialogue",
    "speaker": "Hero"
  }
]
""",
            encoding="utf-8",
        )



def test_projects_api_lists_details_and_scenes(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    create_project(workspace_root, "demo-001", complete=True)
    create_project(workspace_root, "demo-002", complete=False)

    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(workspace_root=workspace_root)))

    assert list_projects(request) == [
        {
            "id": "demo-001",
            "title": "Project demo-001",
            "progress": {
                "images": True,
                "ocr": True,
                "review": True,
                "translation": True,
                "voice": True,
                "scenes": True,
            },
        },
        {
            "id": "demo-002",
            "title": "Project demo-002",
            "progress": {
                "images": True,
                "ocr": True,
                "review": False,
                "translation": False,
                "voice": False,
                "scenes": False,
            },
        },
    ]

    assert get_project("demo-001", request) == {
        "id": "demo-001",
        "title": "Project demo-001",
        "progress": {
            "images": True,
            "ocr": True,
            "review": True,
            "translation": True,
            "voice": True,
            "scenes": True,
        },
        "counts": {
            "frames": 1,
            "voices": 1,
            "scenes": 1,
        },
    }

    assert get_scenes("demo-001", request) == [
        {
            "id": "scene-001",
            "type": "dialogue",
            "image": "images/001.png",
            "subtitleText": "subtitle",
            "audio": "audio/characters/script-bubble-001.wav",
            "durationMs": 1100,
            "speaker": "Hero",
            "stylePreset": "default",
            "cameraMotion": None,
            "transition": "cut",
        }
    ]
