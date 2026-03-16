import shutil
from importlib import import_module

import typer

from apps.api.app.integrations.moyin_tts import MoyinTtsError, MoyinTtsClient
from apps.cli.app.services.ocr_service import validate_ocr_setup
from apps.cli.app.services.translation_service import TranslationServiceError, get_translation_service

REQUIRED_EXECUTABLES = ("python", "node", "ffmpeg")
RENDER_MODULES = (
    ("cv2", "opencv-python"),
    ("numpy", "numpy"),
    ("PIL", "Pillow"),
)


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
        validate_render_setup()
        typer.echo("OK render opencv-python numpy Pillow")
    except RuntimeError as exc:
        failures.append("render")
        typer.echo(f"MISSING render {exc}")

    try:
        validate_ocr_setup()
        typer.echo("OK OCR manga-image-translator")
    except RuntimeError as exc:
        failures.append("ocr")
        typer.echo(f"MISSING OCR {exc}")

    try:
        get_translation_service()
        typer.echo("OK translation manga-image-translator")
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


def validate_render_setup() -> None:
    missing_packages: list[str] = []

    for module_name, package_name in RENDER_MODULES:
        try:
            import_module(module_name)
        except ImportError:
            missing_packages.append(package_name)

    if missing_packages:
        package_list = " ".join(missing_packages)
        raise RuntimeError(
            f"Render dependencies are not installed. Install {package_list}."
        )
