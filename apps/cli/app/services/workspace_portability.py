from __future__ import annotations

import shutil
import tarfile
from pathlib import Path, PurePosixPath

from apps.api.app.services.file_store import FileStore


class WorkspacePortabilityError(RuntimeError):
    pass


def export_workspace_archive(project_dir: Path, archive_path: Path) -> Path:
    project_dir = Path(project_dir)
    archive_path = Path(archive_path)

    if not (project_dir / "project.json").exists():
        raise WorkspacePortabilityError(f"Project not found: {project_dir}")

    resolved_project_dir = project_dir.resolve()
    resolved_archive_path = archive_path.resolve()
    if resolved_archive_path.is_relative_to(resolved_project_dir):
        raise WorkspacePortabilityError("Archive path must be outside the project workspace.")

    archive_path.parent.mkdir(parents=True, exist_ok=True)

    with tarfile.open(archive_path, "w:gz") as archive:
        archive.add(project_dir, arcname=project_dir.name)

    return archive_path


def import_workspace_archive(archive_path: Path, workspace_root: Path) -> Path:
    archive_path = Path(archive_path)
    workspace_root = Path(workspace_root)

    if not archive_path.is_file():
        raise WorkspacePortabilityError(f"Archive not found: {archive_path}")

    with tarfile.open(archive_path, "r:*") as archive:
        members = archive.getmembers()
        project_id = _validate_archive_members(members)
        target_project_dir = workspace_root / project_id
        if target_project_dir.exists():
            raise WorkspacePortabilityError(f"Project already exists: {target_project_dir}")

        workspace_root.mkdir(parents=True, exist_ok=True)

        try:
            archive.extractall(path=workspace_root, members=members, filter="data")
            _validate_imported_project(target_project_dir, project_id)
        except Exception as exc:
            shutil.rmtree(target_project_dir, ignore_errors=True)
            if isinstance(exc, WorkspacePortabilityError):
                raise
            raise WorkspacePortabilityError(f"Failed to import workspace archive: {archive_path}") from exc

    return target_project_dir


def _validate_archive_members(members: list[tarfile.TarInfo]) -> str:
    if not members:
        raise WorkspacePortabilityError("Workspace archive is empty.")

    project_roots: set[str] = set()
    has_project_json = False

    for member in members:
        member_path = _validate_member_path(member)
        project_roots.add(member_path.parts[0])

        if len(member_path.parts) == 2 and member_path.parts[1] == "project.json" and member.isfile():
            has_project_json = True

    if len(project_roots) != 1:
        raise WorkspacePortabilityError("Workspace archive must contain exactly one project directory.")

    project_id = next(iter(project_roots))
    if not has_project_json:
        raise WorkspacePortabilityError("Workspace archive is missing project.json.")

    return project_id


def _validate_member_path(member: tarfile.TarInfo) -> PurePosixPath:
    member_path = PurePosixPath(member.name)

    if member_path.is_absolute():
        raise WorkspacePortabilityError(f"Unsafe archive entry: {member.name}")

    if not member_path.parts:
        raise WorkspacePortabilityError(f"Invalid archive entry: {member.name}")

    if any(part in ("", ".", "..") for part in member_path.parts):
        raise WorkspacePortabilityError(f"Unsafe archive entry: {member.name}")

    if member.issym() or member.islnk() or member.isdev():
        raise WorkspacePortabilityError(f"Unsupported archive entry: {member.name}")

    if not (member.isdir() or member.isfile()):
        raise WorkspacePortabilityError(f"Unsupported archive entry: {member.name}")

    return member_path


def _validate_imported_project(project_dir: Path, expected_project_id: str) -> None:
    project_file = project_dir / "project.json"
    if not project_file.exists():
        raise WorkspacePortabilityError("Imported workspace is missing project.json.")

    project = FileStore(project_dir).load_project()
    if project.id != expected_project_id:
        raise WorkspacePortabilityError(
            f"Imported project id mismatch: expected {expected_project_id}, found {project.id}"
        )
