import shutil

import typer

REQUIRED_EXECUTABLES = ("python", "node", "ffmpeg", "manga-ocr")


def doctor() -> None:
    missing: list[str] = []

    for executable in REQUIRED_EXECUTABLES:
        location = shutil.which(executable)
        if location:
            typer.echo(f"OK {executable} {location}")
            continue

        missing.append(executable)
        typer.echo(f"MISSING {executable}")

    if missing:
        typer.echo(f"Missing {len(missing)} required dependencies.", err=True)
        raise typer.Exit(code=1)

    typer.echo("All required dependencies are available.")
