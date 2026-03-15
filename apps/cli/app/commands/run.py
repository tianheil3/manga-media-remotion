import json
from pathlib import Path

import typer

from apps.api.app.services.file_store import FileStore
from apps.api.app.services.project_integrity import (
    PROGRESS_REQUIRED_FILES,
    ProjectIntegrityError,
    assert_project_integrity,
)

STAGE_ORDER = [
    "import-images",
    "ocr",
    "review",
    "translate",
    "voice",
    "build-scenes",
]


def run_command(
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
        assert_project_integrity(project_dir, required_files=PROGRESS_REQUIRED_FILES)
    except ProjectIntegrityError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error

    status = project_stage_status(project_dir)
    typer.echo(f"Project {project_id} progress")
    for stage in STAGE_ORDER:
        label = "done" if status[stage] else "pending"
        typer.echo(f"[{label}] {stage}")

    next_stage = next((stage for stage in STAGE_ORDER if not status[stage]), None)
    if next_stage is None:
        typer.echo("Next stage: complete")
    else:
        typer.echo(f"Next stage: {next_stage}")


def project_stage_status(project_dir: Path) -> dict[str, bool]:
    store = FileStore(project_dir)
    frames = store.load_frames()
    voices = store.load_voices()
    scenes = store.load_scenes()

    translation_ready = False
    script_path = project_dir / "script" / "script.json"
    if script_path.exists():
        translation_ready = len(json.loads(script_path.read_text(encoding="utf-8"))) > 0

    return {
        "import-images": len(frames) > 0,
        "ocr": any(frame.bubbles for frame in frames),
        "review": any(frame.reviewed_bubbles for frame in frames),
        "translate": translation_ready,
        "voice": any(voice.audio_file for voice in voices),
        "build-scenes": len(scenes) > 0,
    }
