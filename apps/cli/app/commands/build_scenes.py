from pathlib import Path

import typer

from apps.cli.app.services.scene_builder import build_scenes


def build_scenes_command(
    project_id: str = typer.Argument(..., help="Project identifier under the workspace root."),
    padding_ms: int = typer.Option(200, "--padding-ms", help="Padding to add after voiced segments."),
    silent_duration_ms: int = typer.Option(
        1500,
        "--silent-duration-ms",
        help="Fallback duration for silent frames.",
    ),
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
        scenes = build_scenes(
            project_dir,
            padding_ms=padding_ms,
            silent_duration_ms=silent_duration_ms,
        )
    except ValueError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(f"Built {len(scenes)} scenes.")
