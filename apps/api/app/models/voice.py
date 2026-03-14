from pydantic import BaseModel, ConfigDict, Field


class VoiceSegment(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    frame_id: str = Field(alias="frameId")
    text: str
    mode: str
    role: str
    speaker: str | None = None
    voice_preset: str | None = Field(default=None, alias="voicePreset")
    audio_file: str | None = Field(default=None, alias="audioFile")
    transcript: str | None = None
    duration_ms: int | None = Field(default=None, alias="durationMs")
