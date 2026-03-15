from pathlib import Path

import typer

from apps.api.app.services.file_store import FileStore
from apps.cli.app.services.workspace_portability import (
    WorkspacePortabilityError,
    export_workspace_archive,
    import_workspace_archive,
)


def export_workspace_command(
    project_id: str = typer.Argument(..., help="Project identifier under the workspace root."),
    archive_path: Path = typer.Argument(..., help="Destination archive path, typically ending in .tar.gz."),
    workspace_root: Path = typer.Option(
        Path("workspace"),
        "--workspace-root",
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
        help="Directory that stores local-first project workspaces.",
    ),
) -> None:
    project_dir = workspace_root / project_id

    try:
        export_workspace_archive(project_dir, archive_path)
    except WorkspacePortabilityError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(f"Exported workspace {project_id} to {archive_path}")


def import_workspace_command(
    archive_path: Path = typer.Argument(..., help="Previously exported workspace archive."),
    workspace_root: Path = typer.Option(
        Path("workspace"),
        "--workspace-root",
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
        help="Directory that stores local-first project workspaces.",
    ),
) -> None:
    try:
        project_dir = import_workspace_archive(archive_path, workspace_root)
    except WorkspacePortabilityError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    project = FileStore(project_dir).load_project()
    typer.echo(f"Imported workspace {project.id} at {project_dir}")
