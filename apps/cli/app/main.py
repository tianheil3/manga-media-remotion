import typer

from apps.cli.app.commands.doctor import doctor
from apps.cli.app.commands.build_scenes import build_scenes_command
from apps.cli.app.commands.import_images import import_images_command
from apps.cli.app.commands.new import new_project
from apps.cli.app.commands.ocr import ocr_command
from apps.cli.app.commands.open import open_project
from apps.cli.app.commands.run import run_command
from apps.cli.app.commands.review import review_command
from apps.cli.app.commands.translate import translate_command
from apps.cli.app.commands.voice import voice_command

app = typer.Typer(help="CLI workflow for the local-first manga video MVP.")

app.command("build-scenes")(build_scenes_command)
app.command("new")(new_project)
app.command("open")(open_project)
app.command("run")(run_command)
app.command("doctor")(doctor)
app.command("import-images")(import_images_command)
app.command("ocr")(ocr_command)
app.command("review")(review_command)
app.command("translate")(translate_command)
app.command("voice")(voice_command)


if __name__ == "__main__":
    app()
