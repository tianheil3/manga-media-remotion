import os
import shutil

import typer

from apps.api.app.integrations.moyin_tts import MoyinTtsError, MoyinTtsClient
from apps.cli.app.services.ocr_service import validate_ocr_setup
from apps.cli.app.services.translation_service import TranslationServiceError, get_translation_service

REQUIRED_EXECUTABLES = ("python", "node", "ffmpeg")


def doctor() -> None:
    failures: list[str] = []

    for executable in REQUIRED_EXECUTABLES:
        location = shutil.which(executable)
        if location:
            typer.echo(f"OK {executable} {location}")
            continue

        failures.append(executable)
        typer.echo(f"MISSING {executable}")

    try:
        validate_ocr_setup()
        typer.echo("OK OCR manga_ocr import")
    except RuntimeError as exc:
        failures.append("ocr")
        typer.echo(f"MISSING OCR {exc}")

    try:
        provider = os.environ.get("TRANSLATION_PROVIDER", "deepl").strip().lower()
        get_translation_service()
        typer.echo(f"OK translation {provider}")
    except TranslationServiceError as exc:
        failures.append("translation")
        typer.echo(f"MISSING translation {exc}")

    try:
        MoyinTtsClient.from_env()
        typer.echo("OK TTS moyin")
    except MoyinTtsError as exc:
        failures.append("tts")
        typer.echo(f"MISSING TTS {exc}")

    if failures:
        typer.echo(f"Missing {len(failures)} required dependencies or provider checks.", err=True)
        raise typer.Exit(code=1)

    typer.echo("All required dependencies are available.")
