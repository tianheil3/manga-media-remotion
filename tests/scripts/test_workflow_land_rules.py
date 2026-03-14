from pathlib import Path


def test_workflow_defines_the_repository_land_flow_for_merging() -> None:
    workflow = Path("WORKFLOW.md").read_text(encoding="utf-8")

    assert "scripts/land.sh" in workflow
    assert "scripts/verify-strict.sh" in workflow
    assert "When a ticket enters `Merging`" in workflow
    assert "Do not expand scope during `Merging`" in workflow
    assert "Only mark the Linear issue `Done` after `git push origin main` succeeds" in workflow
    assert "`Rework`" in workflow


def test_workflow_documents_the_required_remote_sync_and_squash_merge_steps() -> None:
    workflow = Path("WORKFLOW.md").read_text(encoding="utf-8")

    assert "Fetch `origin/main`" in workflow
    assert "Reset local `main` to `origin/main`" in workflow
    assert "Squash-merge the issue branch into `main`" in workflow
