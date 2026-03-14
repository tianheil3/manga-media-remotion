from pathlib import Path

import typer

from apps.api.app.services.file_store import FileStore


def open_project(
    project_id: str = typer.Argument(..., help="Project identifier under the workspace root."),
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
    project_file = project_dir / "project.json"
    if not project_file.exists():
        typer.echo(f"Project not found: {project_dir}", err=True)
        raise typer.Exit(code=1)

    project = FileStore(project_dir).load_project()
    typer.echo(f"Opened project {project.id} ({project.title}) at {project_dir}")
