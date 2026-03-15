from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from apps.api.app.models.scene import Scene
from apps.api.app.models.voice import VoiceSegment
from apps.api.app.services.file_store import FileStore
from apps.cli.app.services.recording import record_voice_segment
from apps.cli.app.services.scene_sync import resolve_scene_voice_ids, resolve_voice_for_scene

router = APIRouter(prefix="/projects", tags=["voice"])


class SceneUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    subtitle_text: str | None = Field(default=None, alias="subtitleText")
    duration_ms: int = Field(alias="durationMs")
    style_preset: str = Field(alias="stylePreset")


class ReplaceAudioRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    source_audio_path: str = Field(alias="sourceAudioPath")


@router.get("/{project_id}/scene-review")
def get_scene_review(project_id: str, request: Request) -> list[dict[str, object]]:
    store = _project_store(project_id, request)
    scenes = _load_optional_list(store.load_scenes)
    voices = _load_optional_list(store.load_voices)
    scene_voice_ids = resolve_scene_voice_ids(scenes, voices)
    voices_by_id = {voice.id: voice for voice in voices}

    payload: list[dict[str, object]] = []
    for scene in scenes:
        voice_id = scene.voice_id or scene_voice_ids.get(scene.id)
        resolved_voice = voices_by_id.get(voice_id) if voice_id is not None else resolve_voice_for_scene(scene, voices)
        scene_payload = scene.model_dump(mode="json", by_alias=True)
        scene_payload["voiceId"] = voice_id
        scene_payload["audioMetadata"] = _audio_metadata(project_id, resolved_voice)
        payload.append(scene_payload)

    return payload


@router.put("/{project_id}/scenes/{scene_id}")
def update_scene(
    project_id: str,
    scene_id: str,
    payload: SceneUpdate,
    request: Request,
) -> dict[str, object]:
    store = _project_store(project_id, request)
    scenes = _load_optional_list(store.load_scenes)

    updated_scenes: list[Scene] = []
    matched_scene: Scene | None = None
    for scene in scenes:
        if scene.id != scene_id:
            updated_scenes.append(scene)
            continue

        matched_scene = scene.model_copy(
            update={
                "subtitle_text": payload.subtitle_text,
                "duration_ms": payload.duration_ms,
                "style_preset": payload.style_preset,
            }
        )
        updated_scenes.append(matched_scene)

    if matched_scene is None:
        raise HTTPException(status_code=404, detail=f"Unknown scene: {scene_id}")

    store.save_scenes(updated_scenes)
    project = store.load_project()
    project.updated_at = _utc_timestamp()
    store.save_project(project)
    return matched_scene.model_dump(mode="json", by_alias=True)


@router.put("/{project_id}/voices/{voice_id}/audio")
def replace_voice_audio(
    project_id: str,
    voice_id: str,
    payload: ReplaceAudioRequest,
    request: Request,
) -> dict[str, object]:
    try:
        voice = record_voice_segment(
            _project_store(project_id, request).project_dir,
            voice_id,
            source_audio_path=Path(payload.source_audio_path),
        )
    except ValueError as error:
        detail = str(error)
        status_code = 404 if detail.startswith("Unknown voice segment:") else 400
        raise HTTPException(status_code=status_code, detail=detail) from error
    return voice.model_dump(mode="json", by_alias=True)


@router.post("/{project_id}/voices/{voice_id}/skip")
def skip_voice_recording(project_id: str, voice_id: str, request: Request) -> dict[str, object]:
    try:
        voice = record_voice_segment(_project_store(project_id, request).project_dir, voice_id, skip=True)
    except ValueError as error:
        detail = str(error)
        status_code = 404 if detail.startswith("Unknown voice segment:") else 400
        raise HTTPException(status_code=status_code, detail=detail) from error
    return voice.model_dump(mode="json", by_alias=True)


def _audio_metadata(project_id: str, voice: VoiceSegment | None) -> dict[str, object] | None:
    if voice is None:
        return None

    return {
        "id": voice.id,
        "frameId": voice.frame_id,
        "mode": voice.mode,
        "role": voice.role,
        "speaker": voice.speaker,
        "audioFile": voice.audio_file,
        "durationMs": voice.duration_ms,
        "replaceAudioPath": f"/projects/{project_id}/voices/{voice.id}/audio",
        "skipRecordingPath": f"/projects/{project_id}/voices/{voice.id}/skip",
    }


def _load_optional_list(loader):
    try:
        return loader()
    except FileNotFoundError:
        return []


def _project_store(project_id: str, request: Request) -> FileStore:
    project_dir = Path(request.app.state.workspace_root) / project_id
    if not (project_dir / "project.json").exists():
        raise HTTPException(status_code=404, detail="Project not found")
    return FileStore(project_dir)


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
