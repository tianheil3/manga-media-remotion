from pydantic import BaseModel, ConfigDict, Field


class Project(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    title: str
    source_language: str = Field(alias="sourceLanguage")
    image_dir: str = Field(alias="imageDir")
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")
