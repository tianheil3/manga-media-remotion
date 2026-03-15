import json
from pathlib import Path
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.api.app.models.frame import Frame, OcrBubble
from apps.api.app.models.project import Project
from apps.api.app.routes.review import FrameReviewUpdate, ReviewBubbleInput, get_frames, update_frame_review
from apps.api.app.services.file_store import FileStore


def create_project_with_ocr(workspace_root: Path, project_id: str) -> Path:
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
    store.save_frames(
        [
            Frame(
                frameId="frame-001",
                image="images/001.png",
                ocrFile="ocr/001.json",
                bubbles=[
                    OcrBubble(
                        id="bubble-a",
                        text="original-a",
                        bbox={"x": 50, "y": 10, "w": 5, "h": 5},
                        order=1,
                        confidence=0.9,
                        language="ja",
                    ),
                    OcrBubble(
                        id="bubble-b",
                        text="original-b",
                        bbox={"x": 20, "y": 10, "w": 5, "h": 5},
                        order=0,
                        confidence=0.8,
                        language="ja",
                    ),
                ],
                reviewedBubbles=[],
            )
        ]
    )
    return project_dir


def make_request(workspace_root: Path) -> SimpleNamespace:
    return SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(workspace_root=workspace_root)))


def test_get_frames_returns_reviewable_frame_data(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    create_project_with_ocr(workspace_root, "demo-001")
    request = make_request(workspace_root)

    assert get_frames("demo-001", request) == [
        {
            "frameId": "frame-001",
            "image": "/projects/demo-001/media/images/001.png",
            "ocrFile": "ocr/001.json",
            "bubbles": [
                {
                    "id": "bubble-a",
                    "text": "original-a",
                    "bbox": {"x": 50.0, "y": 10.0, "w": 5.0, "h": 5.0},
                    "order": 1,
                    "confidence": 0.9,
                    "language": "ja",
                },
                {
                    "id": "bubble-b",
                    "text": "original-b",
                    "bbox": {"x": 20.0, "y": 10.0, "w": 5.0, "h": 5.0},
                    "order": 0,
                    "confidence": 0.8,
                    "language": "ja",
                },
            ],
            "reviewedBubbles": [],
        }
    ]


def test_update_frame_review_persists_order_kind_text_and_speaker(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    project_dir = create_project_with_ocr(workspace_root, "demo-001")
    request = make_request(workspace_root)

    updated_frame = update_frame_review(
        "demo-001",
        "frame-001",
        FrameReviewUpdate(
            reviewedBubbles=[
                ReviewBubbleInput(
                    sourceBubbleId="bubble-b",
                    textEdited="Narrator line",
                    order=0,
                    kind="narration",
                    speaker="Narrator",
                ),
                ReviewBubbleInput(
                    sourceBubbleId="bubble-a",
                    textEdited="Hero line",
                    order=1,
                    kind="dialogue",
                    speaker="Hero",
                ),
            ]
        ),
        request,
    )

    assert updated_frame["reviewedBubbles"] == [
        {
            "id": "review-bubble-b",
            "sourceBubbleId": "bubble-b",
            "textOriginal": "original-b",
            "textEdited": "Narrator line",
            "order": 0,
            "kind": "narration",
            "speaker": "Narrator",
        },
        {
            "id": "review-bubble-a",
            "sourceBubbleId": "bubble-a",
            "textOriginal": "original-a",
            "textEdited": "Hero line",
            "order": 1,
            "kind": "dialogue",
            "speaker": "Hero",
        },
    ]

    stored_frames = json.loads((project_dir / "script" / "frames.json").read_text(encoding="utf-8"))
    assert stored_frames[0]["reviewedBubbles"] == updated_frame["reviewedBubbles"]
