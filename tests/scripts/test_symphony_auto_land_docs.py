from pathlib import Path


def test_symphony_setup_doc_points_to_the_auto_land_material() -> None:
    setup_doc = Path("docs/setup/symphony.md").read_text(encoding="utf-8")

    assert "docs/verification/symphony-auto-land.md" in setup_doc
    assert "scripts/verify-strict.sh" in setup_doc
    assert "scripts/land.sh" in setup_doc
    assert "npm install" in setup_doc
    assert ".worktrees/symphony-setup" not in setup_doc


def test_symphony_auto_land_verification_checklist_covers_the_safe_end_to_end_flow() -> None:
    checklist = Path("docs/verification/symphony-auto-land.md").read_text(encoding="utf-8")

    assert "safe temporary git repository" in checklist
    assert "scripts/verify-strict.sh" in checklist
    assert "scripts/land.sh" in checklist
    assert "`Merging`" in checklist
    assert "`Done` only after push succeeds" in checklist
    assert "npm install" in checklist
