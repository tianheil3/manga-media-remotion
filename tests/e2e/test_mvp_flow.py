from pathlib import Path

import pytest


def test_mvp_verification_checklist_exists() -> None:
    root = Path(__file__).resolve().parents[2]
    checklist = root / "docs" / "verification" / "mvp-checklist.md"
    manual_flow = root / "tests" / "e2e" / "test_mvp_flow.md"

    assert checklist.exists()
    assert manual_flow.exists()

    checklist_text = checklist.read_text(encoding="utf-8")
    manual_flow_text = manual_flow.read_text(encoding="utf-8")

    for required_phrase in [
        "create a project",
        "import images",
        "run OCR",
        "review text",
        "create voice assets",
        "build scenes",
        "preview",
        "render",
    ]:
        assert required_phrase in checklist_text

    assert "Prerequisites" in manual_flow_text


def test_mvp_manual_flow_is_documented_skip() -> None:
    pytest.skip(
        "Manual MVP verification requires OCR, TTS, and frontend/runtime dependencies. "
        "See docs/verification/mvp-checklist.md and tests/e2e/test_mvp_flow.md."
    )
