from pathlib import Path

import typer

from apps.api.app.services.project_integrity import (
    FULL_REQUIRED_FILES,
    ProjectIntegrityError,
    assert_project_integrity,
    repair_project,
)


def integrity_command(
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
    if not project_dir.exists():
        typer.echo(f"Project not found: {project_dir}", err=True)
        raise typer.Exit(code=1)

    try:
        assert_project_integrity(
            project_dir,
            required_files=FULL_REQUIRED_FILES,
            check_media=True,
            check_scene_voice_refs=True,
        )
    except ProjectIntegrityError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error

    typer.echo("Project integrity OK.")


def repair_command(
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
    if not project_dir.exists():
        typer.echo(f"Project not found: {project_dir}", err=True)
        raise typer.Exit(code=1)

    result = repair_project(project_dir)
    for action in result.actions:
        typer.echo(action)

    if result.issues:
        typer.echo(f"Project integrity check failed for {project_id}:", err=True)
        for issue in result.issues:
            typer.echo(f"- {issue.message}", err=True)
        typer.echo(f"Run `repair {project_id}` to repair common issues.", err=True)
        raise typer.Exit(code=1)

    typer.echo("Project integrity OK.")
