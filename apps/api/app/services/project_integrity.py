import json
from dataclasses import dataclass
from pathlib import Path

from apps.api.app.models.scene import Scene
from apps.api.app.models.voice import VoiceSegment
from apps.api.app.services.file_store import FileStore
from apps.cli.app.services.scene_sync import resolve_scene_voice_ids

FULL_REQUIRED_FILES = (
    "project.json",
    "config.json",
    "script/frames.json",
    "script/voices.json",
    "script/scenes.json",
)
PROGRESS_REQUIRED_FILES = (
    "script/frames.json",
    "script/voices.json",
    "script/scenes.json",
)
FRAME_REVIEW_REQUIRED_FILES = ("script/frames.json",)
SCENE_REVIEW_REQUIRED_FILES = ("script/scenes.json", "script/voices.json")


@dataclass(frozen=True)
class IntegrityIssue:
    message: str
    path: str | None = None
    repairable: bool = False


class ProjectIntegrityError(RuntimeError):
    def __init__(self, project_dir: Path, issues: list[IntegrityIssue]) -> None:
        self.project_dir = Path(project_dir)
        self.issues = issues
        super().__init__(format_integrity_report(self.project_dir, issues))


@dataclass(frozen=True)
class RepairResult:
    actions: list[str]
    issues: list[IntegrityIssue]


def check_project_integrity(
    project_dir: Path,
    *,
    required_files: tuple[str, ...] = (),
    check_media: bool = False,
    check_scene_voice_refs: bool = False,
) -> list[IntegrityIssue]:
    project_dir = Path(project_dir)
    store = FileStore(project_dir)
    issues: list[IntegrityIssue] = []

    frames = None
    voices = None
    scenes = None

    missing_paths = {relative_path for relative_path in required_files if not (project_dir / relative_path).exists()}
    for relative_path in required_files:
        if relative_path not in missing_paths:
            continue
        issues.append(
            IntegrityIssue(
                message=f"Missing project file: {relative_path}",
                path=relative_path,
                repairable=relative_path != "project.json",
            )
        )

    frames_path = project_dir / "script" / "frames.json"
    voices_path = project_dir / "script" / "voices.json"
    scenes_path = project_dir / "script" / "scenes.json"

    if frames_path.exists():
        frames = store.load_frames()
    if voices_path.exists():
        voices = store.load_voices()
    if scenes_path.exists():
        scenes = store.load_scenes()

    if check_media:
        issues.extend(_missing_media_issues(project_dir, frames, voices, scenes))

    if check_scene_voice_refs and scenes is not None and voices is not None:
        issues.extend(_scene_voice_reference_issues(scenes, voices))

    return issues


def assert_project_integrity(
    project_dir: Path,
    *,
    required_files: tuple[str, ...] = (),
    check_media: bool = False,
    check_scene_voice_refs: bool = False,
) -> None:
    issues = check_project_integrity(
        project_dir,
        required_files=required_files,
        check_media=check_media,
        check_scene_voice_refs=check_scene_voice_refs,
    )
    if issues:
        raise ProjectIntegrityError(Path(project_dir), issues)


def format_integrity_report(project_dir: Path, issues: list[IntegrityIssue]) -> str:
    project_id = Path(project_dir).name
    lines = [f"Project integrity check failed for {project_id}:"]
    lines.extend(f"- {issue.message}" for issue in issues)
    lines.append(f"Run `repair {project_id}` to repair common issues.")
    return "\n".join(lines)


def repair_project(project_dir: Path) -> RepairResult:
    project_dir = Path(project_dir)
    store = FileStore(project_dir)
    actions: list[str] = []

    project_path = project_dir / "project.json"
    if project_path.exists() and not (project_dir / "config.json").exists():
        project = store.load_project()
        (project_dir / "config.json").write_text(
            json.dumps({"projectId": project.id}, indent=2) + "\n",
            encoding="utf-8",
        )
        actions.append("Recreated config.json.")

    frames_path = project_dir / "script" / "frames.json"
    if not frames_path.exists():
        store.save_frames([])
        actions.append("Recreated script/frames.json.")

    voices_path = project_dir / "script" / "voices.json"
    if not voices_path.exists():
        store.save_voices([])
        actions.append("Recreated script/voices.json.")

    scenes_path = project_dir / "script" / "scenes.json"
    if not scenes_path.exists():
        store.save_scenes([])
        actions.append("Recreated script/scenes.json.")

    if _repair_scene_voice_links(project_dir):
        actions.append("Resynced scene voice links.")

    issues = check_project_integrity(
        project_dir,
        required_files=FULL_REQUIRED_FILES,
        check_media=True,
        check_scene_voice_refs=True,
    )
    return RepairResult(actions=actions, issues=issues)


def _missing_media_issues(
    project_dir: Path,
    frames,
    voices,
    scenes,
) -> list[IntegrityIssue]:
    issues: list[IntegrityIssue] = []

    for relative_path in _referenced_media_paths(frames, voices, scenes):
        if (project_dir / relative_path).is_file():
            continue
        issues.append(
            IntegrityIssue(
                message=f"Missing media file: {relative_path}",
                path=relative_path,
            )
        )

    return issues


def _referenced_media_paths(frames, voices, scenes) -> list[str]:
    referenced_paths: list[str] = []
    if frames is not None:
        for frame in frames:
            referenced_paths.extend([frame.image, frame.ocr_file])
    if voices is not None:
        for voice in voices:
            if voice.audio_file is not None:
                referenced_paths.append(voice.audio_file)
    if scenes is not None:
        for scene in scenes:
            referenced_paths.append(scene.image)
            if scene.audio is not None:
                referenced_paths.append(scene.audio)

    deduped_paths: list[str] = []
    seen_paths: set[str] = set()
    for relative_path in referenced_paths:
        if relative_path in seen_paths:
            continue
        seen_paths.add(relative_path)
        deduped_paths.append(relative_path)

    return deduped_paths


def _scene_voice_reference_issues(scenes: list[Scene], voices: list[VoiceSegment]) -> list[IntegrityIssue]:
    issues: list[IntegrityIssue] = []
    resolved_voice_ids = resolve_scene_voice_ids(scenes, voices)
    voices_by_id = {voice.id: voice for voice in voices}

    for scene in scenes:
        if scene.type == "silent":
            continue

        resolved_voice_id = scene.voice_id or resolved_voice_ids.get(scene.id)
        voice = voices_by_id.get(resolved_voice_id) if resolved_voice_id is not None else None

        if scene.voice_id is not None and scene.voice_id not in voices_by_id:
            issues.append(
                IntegrityIssue(
                    message=f"Broken scene/voice reference: {scene.id} points to missing voice {scene.voice_id}",
                    path="script/scenes.json",
                    repairable=True,
                )
            )
            continue

        if voice is None:
            issues.append(
                IntegrityIssue(
                    message=f"Broken scene/voice reference: {scene.id} cannot be matched to a voice segment",
                    path="script/scenes.json",
                    repairable=True,
                )
            )
            continue

        if scene.audio != voice.audio_file:
            issues.append(
                IntegrityIssue(
                    message=f"Broken scene/voice reference: {scene.id} audio does not match {voice.id}",
                    path="script/scenes.json",
                    repairable=True,
                )
            )

    return issues


def _repair_scene_voice_links(project_dir: Path) -> bool:
    project_dir = Path(project_dir)
    store = FileStore(project_dir)
    scenes_path = project_dir / "script" / "scenes.json"
    voices_path = project_dir / "script" / "voices.json"
    if not scenes_path.exists() or not voices_path.exists():
        return False

    scenes = store.load_scenes()
    voices = store.load_voices()
    voices_by_id = {voice.id: voice for voice in voices}
    voices_by_audio = {voice.audio_file: voice for voice in voices if voice.audio_file is not None}
    assigned_voice_ids: set[str] = set()
    updated_scenes: list[Scene] = []
    changed = False

    for scene in scenes:
        if scene.type == "silent":
            updated_scenes.append(scene)
            continue

        resolved_voice = None
        if scene.voice_id is not None and scene.voice_id in voices_by_id:
            resolved_voice = voices_by_id[scene.voice_id]
        elif scene.audio is not None and scene.audio in voices_by_audio:
            resolved_voice = voices_by_audio[scene.audio]
        else:
            resolved_voice = next((voice for voice in voices if voice.id not in assigned_voice_ids), None)

        if resolved_voice is None:
            updated_scenes.append(scene)
            continue

        assigned_voice_ids.add(resolved_voice.id)
        repaired_scene = scene.model_copy(
            update={
                "voice_id": resolved_voice.id,
                "audio": resolved_voice.audio_file,
                "speaker": resolved_voice.speaker,
            }
        )
        updated_scenes.append(repaired_scene)
        changed = changed or repaired_scene != scene

    if changed:
        store.save_scenes(updated_scenes)

    return changed
