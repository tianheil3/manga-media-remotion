from pathlib import Path


def test_setup_docs_cover_local_development_requirements() -> None:
    root = Path(__file__).resolve().parents[2]

    readme = (root / "README.md").read_text(encoding="utf-8")
    local_dev = (root / "docs" / "setup" / "local-development.md").read_text(encoding="utf-8")
    moyin_env = (root / "docs" / "setup" / "moyin-env.md").read_text(encoding="utf-8")
    mit_setup = (root / "docs" / "setup" / "manga-image-translator.md").read_text(encoding="utf-8")
    translation_env = (root / "docs" / "setup" / "translation-env.md").read_text(encoding="utf-8")

    assert "Local Development" in readme
    assert "Python" in local_dev
    assert "Node.js" in local_dev
    assert "ffmpeg" in local_dev
    assert "opencv-python" in local_dev
    assert "numpy" in local_dev
    assert "Pillow" in local_dev
    assert "apps/cli" in local_dev
    assert "apps/api" in local_dev
    assert "python -m apps.cli.app.main --help" in local_dev
    assert "python -m apps.cli.app.main export-workspace" in readme
    assert "python -m apps.cli.app.main import-workspace" in readme
    assert "python -m apps.cli.app.main export-workspace" in local_dev
    assert "python -m apps.cli.app.main import-workspace" in local_dev
    assert "uvicorn apps.api.app.main:app --reload" in local_dev
    assert "npm run dev --workspace apps/web" in local_dev
    assert "apps/remotion" in local_dev
    assert "npm run render --workspace apps/remotion -- --help" in local_dev
    assert "npm test --workspace apps/remotion" in local_dev
    assert "doctor" in readme
    assert "doctor" in local_dev
    assert "MANGA_IMAGE_TRANSLATOR_BASE_URL" in local_dev
    assert "MANGA_WORKSPACE_ROOT" in readme
    assert "MANGA_WORKSPACE_ROOT" in local_dev
    assert "MANGA_API_BASE_URL" in readme
    assert "MANGA_API_BASE_URL" in local_dev
    assert "VITE_API_BASE_URL" in local_dev
    assert "bash scripts/smoke-sample-project.sh" in readme
    assert "bash scripts/smoke-sample-project.sh" in local_dev
    assert "tests/fixtures/workspace/demo-001" in readme
    assert "tests/fixtures/workspace/demo-001" in local_dev
    assert "docs/verification/mvp-real-run-2026-03-15.md" in readme
    assert "npm install" in local_dev
    assert "MOYIN_TTS_BASE_URL" in moyin_env
    assert "MOYIN_TTS_API_KEY" in moyin_env
    assert "doctor" in moyin_env
    assert "MANGA_IMAGE_TRANSLATOR_BASE_URL" in translation_env
    assert "MANGA_IMAGE_TRANSLATOR_OCR_PATH" in translation_env
    assert "MANGA_IMAGE_TRANSLATOR_TRANSLATE_PATH" in translation_env
    assert "MANGA_IMAGE_TRANSLATOR_API_KEY" in translation_env
    assert "doctor" in translation_env
    assert "translate/with-form/json" in mit_setup
    assert "/translate/text" in mit_setup
    assert "MANGA_IMAGE_TRANSLATOR_BASE_URL" in mit_setup
    assert "doctor" in mit_setup
    assert "reserved for the Remotion renderer" not in local_dev
    assert "tracked separately" not in local_dev


def test_symphony_docs_cover_backlog_promoter_setup() -> None:
    root = Path(__file__).resolve().parents[2]

    symphony_setup = (root / "docs" / "setup" / "symphony.md").read_text(encoding="utf-8")
    promoter_setup = (root / "docs" / "setup" / "backlog-promoter.md").read_text(encoding="utf-8")

    assert "docs/setup/backlog-promoter.md" in symphony_setup
    assert "config/backlog-promoter.json" in promoter_setup
    assert "LINEAR_API_KEY" in promoter_setup
    assert "python scripts/backlog-promoter.py --once --dry-run" in promoter_setup
    assert "python scripts/backlog-promoter.py --poll --interval-seconds 30" in promoter_setup


def test_operator_runbook_and_release_checklist_cover_the_mvp_handoff_path() -> None:
    root = Path(__file__).resolve().parents[2]

    readme = (root / "README.md").read_text(encoding="utf-8")
    local_dev = (root / "docs" / "setup" / "local-development.md").read_text(encoding="utf-8")
    runbook = (root / "docs" / "setup" / "operator-runbook.md").read_text(encoding="utf-8")
    checklist = (root / "docs" / "verification" / "mvp-checklist.md").read_text(encoding="utf-8")

    assert "docs/setup/operator-runbook.md" in readme
    assert "docs/setup/operator-runbook.md" in local_dev
    assert "docs/verification/mvp-checklist.md" in readme
    assert "docs/verification/mvp-checklist.md" in local_dev

    assert "python -m apps.cli.app.main new" in runbook
    assert "python -m apps.cli.app.main import-images" in runbook
    assert "python -m apps.cli.app.main ocr" in runbook
    assert "python -m apps.cli.app.main review" in runbook
    assert "python -m apps.cli.app.main translate" in runbook
    assert "python -m apps.cli.app.main voice" in runbook
    assert "python -m apps.cli.app.main build-scenes" in runbook
    assert "/render-jobs" in runbook
    assert "workspace/<project-id>/" in runbook
    assert "OCR triage" in runbook
    assert "Translation triage" in runbook
    assert "TTS triage" in runbook
    assert "Media generation triage" in runbook
    assert "Render job triage" in runbook

    assert "Release Readiness Checklist" in checklist
    assert "docs/setup/operator-runbook.md" in checklist
    assert "project creation" in checklist
    assert "final render" in checklist
    assert "docs/verification/mvp-real-run-2026-03-15.md" in checklist
