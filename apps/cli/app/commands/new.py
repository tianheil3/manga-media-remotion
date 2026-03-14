import json
from datetime import datetime, timezone
from pathlib import Path

import typer

from apps.api.app.models.project import Project
from apps.api.app.services.file_store import FileStore

VALID_SOURCE_LANGUAGES = {"ja", "zh", "en"}


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def new_project(
    project_id: str = typer.Argument(..., help="Project identifier used in workspace/<project-id>."),
    title: str = typer.Option(..., "--title", help="Human-readable project title."),
    workspace_root: Path = typer.Option(
        Path("workspace"),
        "--workspace-root",
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
        help="Directory that stores local-first project workspaces.",
    ),
    source_language: str = typer.Option(
        "ja",
        "--source-language",
        help="Primary source language for imported manga text.",
    ),
) -> None:
    if source_language not in VALID_SOURCE_LANGUAGES:
        raise typer.BadParameter("source language must be one of: ja, zh, en")

    project_dir = workspace_root / project_id
    if project_dir.exists():
        typer.echo(f"Project already exists: {project_dir}", err=True)
        raise typer.Exit(code=1)

    project_dir.mkdir(parents=True, exist_ok=True)
    for directory_name in ("images", "ocr", "audio", "renders", "cache"):
        (project_dir / directory_name).mkdir(parents=True, exist_ok=True)

    timestamp = _utc_timestamp()
    store = FileStore(project_dir)
    store.save_project(
        Project(
            id=project_id,
            title=title,
            sourceLanguage=source_language,
            imageDir="images",
            createdAt=timestamp,
            updatedAt=timestamp,
        )
    )
    store.save_frames([])
    store.save_voices([])
    store.save_scenes([])

    _write_json(project_dir / "config.json", {"projectId": project_id})

    typer.echo(f"Created project {project_id} at {project_dir}")
