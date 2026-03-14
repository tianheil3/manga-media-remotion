from pathlib import Path

import typer

from apps.cli.app.services.image_import import import_images


def import_images_command(
    project_id: str = typer.Argument(..., help="Project identifier under the workspace root."),
    image_paths: list[Path] = typer.Argument(..., help="Source image paths in desired import order."),
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

    try:
        frames = import_images(project_dir, image_paths)
    except ValueError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(f"Imported {len(frames)} images into {project_dir}")
