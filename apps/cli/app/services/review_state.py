import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from apps.api.app.models.frame import Frame, ReviewedBubble
from apps.api.app.services.file_store import FileStore


class ReviewEntry(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    source_bubble_id: str = Field(alias="sourceBubbleId")
    text_edited: str = Field(alias="textEdited")
    order: int
    kind: Literal["dialogue", "narration", "sfx", "ignore"]
    speaker: str | None = None


def load_review_entries(review_file: Path) -> list[ReviewEntry]:
    payload = json.loads(review_file.read_text(encoding="utf-8"))
    return [ReviewEntry.model_validate(item) for item in payload]


def apply_review(
    project_dir: Path,
    frame_id: str,
    review_entries: list[ReviewEntry] | None = None,
    *,
    skip: bool = False,
) -> Frame:
    if skip and review_entries:
        raise ValueError("Cannot provide review entries when skipping a frame.")
    if not skip and review_entries is None:
        raise ValueError("Review entries are required unless --skip is used.")

    store = FileStore(project_dir)
    frames = store.load_frames()

    updated_frames: list[Frame] = []
    matched_frame: Frame | None = None

    for frame in frames:
        if frame.frame_id != frame_id:
            updated_frames.append(frame)
            continue

        matched_frame = frame
        if skip:
            updated_frames.append(frame)
            continue

        source_bubbles = {bubble.id: bubble for bubble in frame.bubbles}
        reviewed_bubbles: list[ReviewedBubble] = []
        for entry in sorted(review_entries or [], key=lambda item: item.order):
            source_bubble = source_bubbles.get(entry.source_bubble_id)
            if source_bubble is None:
                raise ValueError(f"Unknown OCR bubble: {entry.source_bubble_id}")

            reviewed_bubbles.append(
                ReviewedBubble(
                    id=f"review-{entry.source_bubble_id}",
                    sourceBubbleId=entry.source_bubble_id,
                    textOriginal=source_bubble.text,
                    textEdited=entry.text_edited,
                    order=entry.order,
                    kind=entry.kind,
                    speaker=entry.speaker,
                )
            )

        updated_frames.append(frame.model_copy(update={"reviewed_bubbles": reviewed_bubbles}))

    if matched_frame is None:
        raise ValueError(f"Unknown frame: {frame_id}")

    store.save_frames(updated_frames)
    project = store.load_project()
    project.updated_at = _utc_timestamp()
    store.save_project(project)

    return next(frame for frame in updated_frames if frame.frame_id == frame_id)


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
