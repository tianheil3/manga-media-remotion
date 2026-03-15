from pydantic import BaseModel, ConfigDict, Field


class Scene(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    type: str
    image: str
    subtitle_text: str | None = Field(default=None, alias="subtitleText")
    voice_id: str | None = Field(default=None, alias="voiceId")
    audio: str | None = None
    duration_ms: int = Field(alias="durationMs")
    speaker: str | None = None
    style_preset: str = Field(alias="stylePreset")
    camera_motion: str | None = Field(default=None, alias="cameraMotion")
    transition: str | None = None
