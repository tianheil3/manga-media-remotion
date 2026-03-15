# TIA-40 Workspace Portability Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a portable single-project workspace export/import flow for `workspace/<project-id>/` and cover it with automated tests.

**Architecture:** Keep the current project directory as the source of truth. Add a small CLI service that packages a project directory as a safe `.tar.gz` archive and restores that archive into another workspace root after structural validation. Reuse the existing integrity and progress commands for post-import verification.

**Tech Stack:** Python, Typer, `tarfile`, pytest

---

### Task 1: Add failing CLI portability coverage

**Files:**
- Create: `apps/cli/tests/test_workspace_portability.py`
- Modify: `tests/e2e/test_sample_project_smoke.py`

**Steps:**
1. Add a test that creates a project, exports it, imports it into a fresh workspace root, and asserts the imported workspace preserves the expected files.
2. Run the focused CLI test and verify it fails because the portability commands do not exist yet.
3. Add a smoke assertion that an exported archive of the committed fixture can be imported and then still passes the existing CLI progress flow.
4. Run the focused smoke test and verify it fails for the same reason.

### Task 2: Implement archive export/import commands and service

**Files:**
- Create: `apps/cli/app/services/workspace_portability.py`
- Create: `apps/cli/app/commands/workspace_portability.py`
- Modify: `apps/cli/app/main.py`

**Steps:**
1. Implement archive export rooted at `<project-id>/`.
2. Implement safe import with path validation, `project.json` validation, and destination collision checks.
3. Wire `export-workspace` and `import-workspace` into the CLI.
4. Re-run the focused portability tests and verify they pass.

### Task 3: Document the portability flow

**Files:**
- Modify: `README.md`
- Modify: `docs/setup/local-development.md`
- Modify: `tests/docs/test_setup_docs.py`

**Steps:**
1. Document the CLI export/import commands in the local development docs and README.
2. Extend the setup docs test so the new commands are required.
3. Run the docs test and verify it passes.

### Task 4: Run ticket validation and update Linear

**Files:**
- Modify: Linear `## Codex Workpad` comment

**Steps:**
1. Run `python -m pytest apps/cli/tests/test_workspace_portability.py tests/e2e/test_sample_project_smoke.py tests/docs/test_setup_docs.py -v`.
2. Run `python -m pytest apps/cli/tests apps/api/tests tests/e2e/test_sample_project_smoke.py tests/docs -v`.
3. Update the workpad with failing-test and passing-test evidence, final validation output, and any residual risks.
