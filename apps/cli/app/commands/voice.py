from pathlib import Path

import typer

from apps.api.app.integrations.moyin_tts import MoyinTtsError
from apps.cli.app.services.voice_generation import generate_voices


def voice_command(
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

    try:
        voices = generate_voices(project_dir)
    except (MoyinTtsError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(f"Generated {len(voices)} voice segments.")
