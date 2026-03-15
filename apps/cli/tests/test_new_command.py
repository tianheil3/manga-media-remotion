import builtins
import json
from pathlib import Path
import sys
import types

from typer.testing import CliRunner

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import apps.cli.app.commands.doctor as doctor_command
from apps.cli.app.main import app

runner = CliRunner()


def create_project(workspace_root: Path) -> Path:
    result = runner.invoke(
        app,
        [
            "new",
            "demo-001",
            "--title",
            "Demo Project",
            "--workspace-root",
            str(workspace_root),
        ],
    )

    assert result.exit_code == 0, result.stdout
    return workspace_root / "demo-001"


def test_new_creates_workspace_structure_and_base_files(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"

    result = runner.invoke(
        app,
        [
            "new",
            "demo-001",
            "--title",
            "Demo Project",
            "--workspace-root",
            str(workspace_root),
        ],
    )

    assert result.exit_code == 0, result.stdout

    project_dir = workspace_root / "demo-001"
    assert project_dir.is_dir()
    assert (project_dir / "images").is_dir()
    assert (project_dir / "ocr").is_dir()
    assert (project_dir / "script").is_dir()
    assert (project_dir / "audio").is_dir()
    assert (project_dir / "renders").is_dir()
    assert (project_dir / "cache").is_dir()

    project_payload = json.loads((project_dir / "project.json").read_text(encoding="utf-8"))
    assert project_payload["id"] == "demo-001"
    assert project_payload["title"] == "Demo Project"
    assert project_payload["sourceLanguage"] == "ja"
    assert project_payload["imageDir"] == "images"
    assert project_payload["createdAt"]
    assert project_payload["updatedAt"]

    config_payload = json.loads((project_dir / "config.json").read_text(encoding="utf-8"))
    assert config_payload["projectId"] == "demo-001"

    assert json.loads((project_dir / "script" / "frames.json").read_text(encoding="utf-8")) == []
    assert json.loads((project_dir / "script" / "voices.json").read_text(encoding="utf-8")) == []
    assert json.loads((project_dir / "script" / "scenes.json").read_text(encoding="utf-8")) == []


def test_open_resolves_an_existing_project(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    project_dir = create_project(workspace_root)

    result = runner.invoke(
        app,
        ["open", "demo-001", "--workspace-root", str(workspace_root)],
    )

    assert result.exit_code == 0, result.stdout
    assert "demo-001" in result.stdout
    assert "Demo Project" in result.stdout
    assert str(project_dir) in result.stdout


def test_doctor_reports_missing_dependencies(monkeypatch) -> None:
    dependencies = {
        "python": "/usr/bin/python3",
        "node": "/usr/bin/node",
        "ffmpeg": None,
    }
    fake_manga_ocr = types.ModuleType("manga_ocr")
    fake_manga_ocr.MangaOcr = object
    monkeypatch.setitem(sys.modules, "manga_ocr", fake_manga_ocr)
    monkeypatch.setenv("TRANSLATION_PROVIDER", "deepl")
    monkeypatch.setenv("DEEPL_API_KEY", "secret-token")
    monkeypatch.setenv("MOYIN_TTS_BASE_URL", "https://example.invalid/tts")
    monkeypatch.setenv("MOYIN_TTS_API_KEY", "secret-token")

    monkeypatch.setattr(
        doctor_command.shutil,
        "which",
        lambda executable: dependencies.get(executable),
    )

    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 1, result.stdout
    assert "OK python" in result.stdout
    assert "OK node" in result.stdout
    assert "MISSING ffmpeg" in result.stdout


def test_doctor_reports_missing_provider_prerequisites(monkeypatch) -> None:
    dependencies = {
        "python": "/usr/bin/python3",
        "node": "/usr/bin/node",
        "ffmpeg": "/usr/bin/ffmpeg",
    }
    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "manga_ocr":
            raise ImportError("No module named 'manga_ocr'")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.delenv("TRANSLATION_PROVIDER", raising=False)
    monkeypatch.delenv("DEEPL_API_KEY", raising=False)
    monkeypatch.delenv("DEEPL_BASE_URL", raising=False)
    monkeypatch.delenv("MOYIN_TTS_BASE_URL", raising=False)
    monkeypatch.delenv("MOYIN_TTS_API_KEY", raising=False)
    monkeypatch.setattr(builtins, "__import__", fake_import)
    monkeypatch.setattr(
        doctor_command.shutil,
        "which",
        lambda executable: dependencies.get(executable),
    )

    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 1, result.stdout
    assert "MangaOCR is not installed" in result.stdout
    assert "TRANSLATION_PROVIDER=deepl" in result.stdout
    assert "DEEPL_API_KEY" in result.stdout
    assert "MOYIN_TTS_BASE_URL" in result.stdout
    assert "MOYIN_TTS_API_KEY" in result.stdout


def test_doctor_reports_configured_provider_prerequisites(monkeypatch) -> None:
    dependencies = {
        "python": "/usr/bin/python3",
        "node": "/usr/bin/node",
        "ffmpeg": "/usr/bin/ffmpeg",
    }
    fake_manga_ocr = types.ModuleType("manga_ocr")
    fake_manga_ocr.MangaOcr = object
    monkeypatch.setitem(sys.modules, "manga_ocr", fake_manga_ocr)
    monkeypatch.setenv("TRANSLATION_PROVIDER", "deepl")
    monkeypatch.setenv("DEEPL_API_KEY", "secret-token")
    monkeypatch.setenv("MOYIN_TTS_BASE_URL", "https://example.invalid/tts")
    monkeypatch.setenv("MOYIN_TTS_API_KEY", "secret-token")
    monkeypatch.setattr(
        doctor_command.shutil,
        "which",
        lambda executable: dependencies.get(executable),
    )

    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 0, result.stdout
    assert "OK python" in result.stdout
    assert "OK node" in result.stdout
    assert "OK ffmpeg" in result.stdout
    assert "OK OCR" in result.stdout
    assert "OK translation" in result.stdout
    assert "OK TTS" in result.stdout
