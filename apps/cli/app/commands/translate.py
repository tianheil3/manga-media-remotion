from pathlib import Path

import typer

import apps.cli.app.services.translation_service as translation_service
from apps.api.app.services.file_store import FileStore
from apps.cli.app.services.script_builder import load_script_overrides, run_translation


def translate_command(
    project_id: str = typer.Argument(..., help="Project identifier under the workspace root."),
    target_language: str = typer.Option("zh", "--target-language", help="Target translation language."),
    overrides_file: Path | None = typer.Option(
        None,
        "--overrides-file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
        help="Optional JSON overrides for translated, voice, or subtitle text.",
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

    store = FileStore(project_dir)
    project = store.load_project()
    overrides = load_script_overrides(overrides_file)

    try:
        active_translation_service = translation_service.get_translation_service()
    except translation_service.TranslationServiceError as exc:
        active_translation_service = translation_service.DeferredFailureTranslationService(exc)

    try:
        entries = run_translation(
            project_dir,
            project=project,
            translation_service=active_translation_service,
            target_language=target_language,
            overrides=overrides,
        )
    except (ValueError, translation_service.TranslationServiceError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(f"Generated {len(entries)} script entries.")
