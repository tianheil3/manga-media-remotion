# TIA-36 Real MVP Workflow Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Execute the current MVP flow against a fresh local project and check in a verified run record with exact commands, artifacts, prerequisites, and gaps.

**Architecture:** Reuse the existing CLI pipeline as the source of truth for project creation, import, OCR, review, translation, voice, and scene building. Use the repository's local API, web review app, and Remotion preview path only where the current environment can actually exercise them, and explicitly document any remaining manual or external-provider steps instead of papering over them.

**Tech Stack:** Python CLI, FastAPI, React/Vite web app, Remotion, pytest, Linear workpad comment

---

### Task 1: Establish the runnable baseline

**Files:**
- Modify: `docs/verification/mvp-checklist.md`
- Test: `tests/e2e/test_mvp_flow.py`

**Steps:**
1. Sync the workspace with `origin/main` and record the result in the Linear `## Codex Workpad` comment.
2. Capture the current baseline that only a checklist and documented skip exist for MVP verification.
3. Inspect the current CLI and setup docs to identify the exact commands and prerequisites for each MVP stage.

### Task 2: Execute the MVP workflow against a fresh project

**Files:**
- Modify: `docs/verification/mvp-checklist.md`
- Create: `docs/verification/mvp-real-run-2026-03-15.md`

**Steps:**
1. Create a fresh workspace project with the CLI.
2. Import a real image into that project and run the supported pipeline stages in order.
3. Record the exact commands, outputs, generated files, and stage-specific blockers or manual steps.
4. Exercise the local API/web/remotion path enough to document what is verified versus what remains manual in this environment.

### Task 3: Check in the verified documentation

**Files:**
- Modify: `docs/verification/mvp-checklist.md`
- Create or modify: `docs/verification/mvp-real-run-2026-03-15.md`
- Modify: `tests/e2e/test_mvp_flow.py`

**Steps:**
1. Update the checklist so it points to the real execution record.
2. Add the run log with commands, outputs, artifacts, prerequisites, and gaps.
3. Tighten the documentation test so the checked-in run record is required.

### Task 4: Validate and hand off

**Files:**
- Modify: Linear `## Codex Workpad` comment

**Steps:**
1. Run `python -m pytest apps/api/tests apps/cli/tests tests/docs -v`.
2. Run any focused regression checks needed for the updated MVP docs.
3. Update the workpad with final validation, artifacts, and residual risks.
