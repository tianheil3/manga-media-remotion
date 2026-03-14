from pathlib import Path


def test_setup_docs_cover_local_development_requirements() -> None:
    root = Path(__file__).resolve().parents[2]

    readme = (root / "README.md").read_text(encoding="utf-8")
    local_dev = (root / "docs" / "setup" / "local-development.md").read_text(encoding="utf-8")
    moyin_env = (root / "docs" / "setup" / "moyin-env.md").read_text(encoding="utf-8")
    mangaocr = (root / "docs" / "setup" / "mangaocr.md").read_text(encoding="utf-8")

    assert "Local Development" in readme
    assert "Python" in local_dev
    assert "Node.js" in local_dev
    assert "apps/cli" in local_dev
    assert "apps/api" in local_dev
    assert "apps/remotion" in local_dev
    assert "MOYIN_TTS_BASE_URL" in moyin_env
    assert "MOYIN_TTS_API_KEY" in moyin_env
    assert "manga-ocr" in mangaocr
    assert "pip install" in mangaocr
