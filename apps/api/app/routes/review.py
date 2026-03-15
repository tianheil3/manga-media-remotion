from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from apps.api.app.models.frame import Frame
from apps.api.app.services.project_media import project_dir_or_404, project_media_url
from apps.api.app.services.file_store import FileStore
from apps.api.app.services.project_integrity import (
    FRAME_REVIEW_REQUIRED_FILES,
    ProjectIntegrityError,
    assert_project_integrity,
)
from apps.cli.app.services.review_state import ReviewEntry, apply_review

router = APIRouter(prefix="/projects", tags=["review"])


class ReviewBubbleInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    source_bubble_id: str = Field(alias="sourceBubbleId")
    text_edited: str = Field(alias="textEdited")
    order: int
    kind: Literal["dialogue", "narration", "sfx", "ignore"]
    speaker: str | None = None


class FrameReviewUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    reviewed_bubbles: list[ReviewBubbleInput] = Field(default_factory=list, alias="reviewedBubbles")
    skip: bool = False


@router.get("/{project_id}/frames")
def get_frames(project_id: str, request: Request) -> list[dict[str, object]]:
    store = _project_store(project_id, request)
    try:
        assert_project_integrity(store.project_dir, required_files=FRAME_REVIEW_REQUIRED_FILES)
    except ProjectIntegrityError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    frames = store.load_frames()

    return [_frame_payload(project_id, frame) for frame in frames]


@router.put("/{project_id}/frames/{frame_id}/review")
def update_frame_review(
    project_id: str,
    frame_id: str,
    payload: FrameReviewUpdate,
    request: Request,
) -> dict[str, object]:
    project_dir = _project_dir(project_id, request)
    review_entries = [
        ReviewEntry(
            sourceBubbleId=bubble.source_bubble_id,
            textEdited=bubble.text_edited,
            order=bubble.order,
            kind=bubble.kind,
            speaker=bubble.speaker,
        )
        for bubble in payload.reviewed_bubbles
    ]

    try:
        updated_frame = apply_review(
            project_dir,
            frame_id,
            review_entries if not payload.skip else None,
            skip=payload.skip,
        )
    except ValueError as error:
        detail = str(error)
        if detail.startswith("Unknown frame:"):
            raise HTTPException(status_code=404, detail=detail) from error
        raise HTTPException(status_code=400, detail=detail) from error

    return _frame_payload(project_id, updated_frame)


def _project_store(project_id: str, request: Request) -> FileStore:
    return FileStore(_project_dir(project_id, request))


def _project_dir(project_id: str, request: Request) -> Path:
    return project_dir_or_404(project_id, request)


def _frame_payload(project_id: str, frame: Frame) -> dict[str, object]:
    payload = frame.model_dump(mode="json", by_alias=True)
    payload["image"] = project_media_url(project_id, frame.image)
    return payload
