import json
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from apps.api.app.models.frame import Frame
from apps.api.app.models.project import Project
from apps.api.app.models.scene import Scene
from apps.api.app.models.voice import VoiceSegment

ModelT = TypeVar("ModelT", bound=BaseModel)


class FileStore:
    def __init__(self, project_dir: Path) -> None:
        self.project_dir = Path(project_dir)
        self.script_dir = self.project_dir / "script"

    def save_project(self, project: Project) -> None:
        self._write_model(self.project_dir / "project.json", project)

    def load_project(self) -> Project:
        return self._read_model(self.project_dir / "project.json", Project)

    def save_frames(self, frames: list[Frame]) -> None:
        self._write_models(self.script_dir / "frames.json", frames)

    def load_frames(self) -> list[Frame]:
        return self._read_models(self.script_dir / "frames.json", Frame)

    def save_voices(self, voices: list[VoiceSegment]) -> None:
        self._write_models(self.script_dir / "voices.json", voices)

    def load_voices(self) -> list[VoiceSegment]:
        return self._read_models(self.script_dir / "voices.json", VoiceSegment)

    def save_scenes(self, scenes: list[Scene]) -> None:
        self._write_models(self.script_dir / "scenes.json", scenes)

    def load_scenes(self) -> list[Scene]:
        return self._read_models(self.script_dir / "scenes.json", Scene)

    def _write_model(self, path: Path, model: BaseModel) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(model.model_dump(mode="json", by_alias=True), indent=2) + "\n",
            encoding="utf-8",
        )

    def _read_model(self, path: Path, model_type: type[ModelT]) -> ModelT:
        data = json.loads(path.read_text(encoding="utf-8"))
        return model_type.model_validate(data)

    def _write_models(self, path: Path, models: list[BaseModel]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = [model.model_dump(mode="json", by_alias=True) for model in models]
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    def _read_models(self, path: Path, model_type: type[ModelT]) -> list[ModelT]:
        data = json.loads(path.read_text(encoding="utf-8"))
        return [model_type.model_validate(item) for item in data]
