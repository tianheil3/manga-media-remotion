from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class BoundingBox(BaseModel):
    x: float
    y: float
    w: float
    h: float


class OcrBubble(BaseModel):
    id: str
    text: str
    bbox: BoundingBox
    order: int
    confidence: float
    language: Literal["ja", "zh", "en"]


class ReviewedBubble(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    source_bubble_id: str = Field(alias="sourceBubbleId")
    text_original: str = Field(alias="textOriginal")
    text_edited: str = Field(alias="textEdited")
    order: int
    kind: Literal["dialogue", "narration", "sfx", "ignore"]
    speaker: str | None = None


class Frame(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    frame_id: str = Field(alias="frameId")
    image: str
    ocr_file: str = Field(alias="ocrFile")
    bubbles: list[OcrBubble] = Field(default_factory=list)
    reviewed_bubbles: list[ReviewedBubble] = Field(default_factory=list, alias="reviewedBubbles")
