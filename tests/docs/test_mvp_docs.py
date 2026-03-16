from pathlib import Path


def test_mvp_verification_docs_include_a_real_run_record() -> None:
    checklist = Path("docs/verification/mvp-checklist.md").read_text(encoding="utf-8")
    run_record = Path("docs/verification/mvp-real-run-2026-03-15.md").read_text(encoding="utf-8")

    assert "mvp-real-run-2026-03-15.md" in checklist
    assert "tia-36-mvp-demo" in run_record
    assert "tests/fixtures/workspace/demo-001/images/001.png" in run_record
    assert "python -m apps.cli.app.main new tia-36-mvp-demo" in run_record
    assert "python -m apps.cli.app.main import-images tia-36-mvp-demo" in run_record
    assert "python -m apps.cli.app.main ocr tia-36-mvp-demo" in run_record
    assert "Generated 1 script entries." in run_record
    assert "Generated 1 voice segments." in run_record
    assert "render-preview-002" in run_record
    assert "render-final-002" in run_record
    assert "Missing project.json for render job." in run_record
    assert 'MANGA_WORKSPACE_ROOT="$(pwd)/workspace" uvicorn' in run_record
    assert "MISSING ffmpeg" in run_record
    assert "predates the MIT service migration in TIA-43" in run_record
