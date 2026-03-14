from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.api.app.models.frame import Frame, OcrBubble, ReviewedBubble
from apps.api.app.models.project import Project
from apps.api.app.models.scene import Scene
from apps.api.app.models.voice import VoiceSegment
from apps.api.app.services.file_store import FileStore


def test_file_store_round_trip(tmp_path: Path) -> None:
    store = FileStore(tmp_path / "workspace" / "demo-001")

    project = Project(
        id="demo-001",
        title="Demo Project",
        source_language="ja",
        image_dir="images",
        created_at="2026-03-14T00:00:00Z",
        updated_at="2026-03-14T00:00:00Z",
    )
    frames = [
        Frame(
            frame_id="frame-001",
            image="images/001.png",
            ocr_file="ocr/001.json",
            bubbles=[
                OcrBubble(
                    id="bubble-001",
                    text="hello",
                    bbox={"x": 1, "y": 2, "w": 3, "h": 4},
                    order=0,
                    confidence=0.95,
                    language="ja",
                )
            ],
            reviewed_bubbles=[
                ReviewedBubble(
                    id="review-001",
                    source_bubble_id="bubble-001",
                    text_original="hello",
                    text_edited="hello there",
                    order=0,
                    kind="dialogue",
                    speaker="narrator",
                )
            ],
        )
    ]
    voices = [
        VoiceSegment(
            id="voice-001",
            frame_id="frame-001",
            text="hello there",
            mode="tts",
            role="narrator",
            duration_ms=1200,
        )
    ]
    scenes = [
        Scene(
            id="scene-001",
            type="narration",
            image="images/001.png",
            subtitle_text="hello there",
            audio="audio/narration/001.wav",
            duration_ms=1200,
            style_preset="default",
            transition="cut",
        )
    ]

    store.save_project(project)
    store.save_frames(frames)
    store.save_voices(voices)
    store.save_scenes(scenes)

    assert (store.project_dir / "project.json").exists()
    assert (store.project_dir / "script" / "frames.json").exists()
    assert (store.project_dir / "script" / "voices.json").exists()
    assert (store.project_dir / "script" / "scenes.json").exists()

    loaded_project = store.load_project()
    loaded_frames = store.load_frames()
    loaded_voices = store.load_voices()
    loaded_scenes = store.load_scenes()

    assert loaded_project == project
    assert loaded_frames == frames
    assert loaded_voices == voices
    assert loaded_scenes == scenes
