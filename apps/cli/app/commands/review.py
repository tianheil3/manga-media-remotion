from pathlib import Path

import typer

from apps.cli.app.services.review_state import apply_review, load_review_entries


def review_command(
    project_id: str = typer.Argument(..., help="Project identifier under the workspace root."),
    frame_id: str = typer.Argument(..., help="Frame identifier to review."),
    review_file: Path | None = typer.Option(
        None,
        "--review-file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
        help="JSON file containing reviewed bubble overrides for the selected frame.",
    ),
    skip: bool = typer.Option(False, "--skip", help="Skip this frame for now without editing it."),
    workspace_root: Path = typer.Option(
        Path("workspace"),
        "--workspace-root",
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
        help="Directory that stores local-first project workspaces.",
    ),
) -> None:
    if skip and review_file is not None:
        typer.echo("Cannot use --skip together with --review-file.", err=True)
        raise typer.Exit(code=1)
    if not skip and review_file is None:
        typer.echo("Provide --review-file or use --skip.", err=True)
        raise typer.Exit(code=1)

    project_dir = workspace_root / project_id
    project_file = project_dir / "project.json"
    if not project_file.exists():
        typer.echo(f"Project not found: {project_dir}", err=True)
        raise typer.Exit(code=1)

    try:
        review_entries = None if review_file is None else load_review_entries(review_file)
        frame = apply_review(project_dir, frame_id, review_entries, skip=skip)
    except ValueError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    if skip:
        typer.echo(f"Skipped review for {frame.frame_id}.")
    else:
        typer.echo(f"Saved review for {frame.frame_id}.")
