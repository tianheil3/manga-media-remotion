# Symphony Auto-Land Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a repository-defined strict verification and squash-merge landing workflow so Symphony can move issues from `Merging` to a successful push on `main`.

**Architecture:** Keep the implementation repository-local and deterministic. Add shell scripts for strict validation and landing, then update `WORKFLOW.md` so Symphony treats `Merging` as a landing-only phase that runs the repository scripts instead of free-form merge behavior.

**Tech Stack:** Bash, Git, Symphony `WORKFLOW.md`, pytest, npm test commands

---

### Task 1: Define Strict Validation Contract

**Files:**
- Create: `scripts/verify-strict.sh`
- Create: `tests/scripts/test_verify_strict.py`
- Modify: `README.md`

**Step 1: Write the failing test**

Write tests that verify:
- the script exists
- the script exits non-zero when a required command fails
- the script executes repository default validation commands in order

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/scripts/test_verify_strict.py -v`
Expected: FAIL because the script and test fixtures do not exist yet.

**Step 3: Write minimal implementation**

Implement `scripts/verify-strict.sh` with the smallest strict validation contract needed for this repository and document its purpose in `README.md`.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/scripts/test_verify_strict.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add scripts/verify-strict.sh tests/scripts/test_verify_strict.py README.md
git commit -m "feat: add strict verification script"
```

### Task 2: Define Landing Script Behavior

**Files:**
- Create: `scripts/land.sh`
- Create: `tests/scripts/test_land_script.py`

**Step 1: Write the failing test**

Write tests that verify:
- the script rejects execution without a target work branch
- the script invokes strict verification before merge
- the script performs squash merge semantics instead of preserving source commits
- the script refuses to mark success before push

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/scripts/test_land_script.py -v`
Expected: FAIL because the land script does not exist.

**Step 3: Write minimal implementation**

Implement `scripts/land.sh` to:
- accept or detect a work branch
- run `scripts/verify-strict.sh`
- fetch `origin/main`
- reset local `main` to `origin/main`
- squash merge the work branch
- commit using an issue-aware message
- push `main`

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/scripts/test_land_script.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add scripts/land.sh tests/scripts/test_land_script.py
git commit -m "feat: add symphony land script"
```

### Task 3: Add Failure Reporting Conventions

**Files:**
- Modify: `scripts/land.sh`
- Modify: `scripts/verify-strict.sh`
- Create: `docs/setup/symphony-land.md`

**Step 1: Write the failing test**

Write tests that verify:
- validation failures produce actionable output
- merge conflicts return non-zero with clear context
- push failures are surfaced without false success messages

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/scripts/test_land_script.py -v`
Expected: FAIL because failure-reporting behavior is not implemented yet.

**Step 3: Write minimal implementation**

Refine the scripts so they emit clear machine-readable and human-readable failure signals, then document the behavior in `docs/setup/symphony-land.md`.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/scripts/test_land_script.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add scripts/land.sh scripts/verify-strict.sh docs/setup/symphony-land.md
git commit -m "docs: define symphony land failure handling"
```

### Task 4: Update WORKFLOW.md for Merging State

**Files:**
- Modify: `WORKFLOW.md`
- Test: `tests/scripts/test_workflow_land_rules.py`

**Step 1: Write the failing test**

Write tests that verify:
- `WORKFLOW.md` explicitly instructs `Merging` to run the repository land script
- the workflow states that push success is required before marking `Done`
- the workflow forbids expanding scope during `Merging`

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/scripts/test_workflow_land_rules.py -v`
Expected: FAIL because the workflow text is still too ambiguous.

**Step 3: Write minimal implementation**

Update `WORKFLOW.md` so `Merging` becomes a landing-only state tied to `scripts/land.sh`, with strict validation and explicit failure handling.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/scripts/test_workflow_land_rules.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add WORKFLOW.md tests/scripts/test_workflow_land_rules.py
git commit -m "feat: define symphony merging workflow"
```

### Task 5: Add Script Smoke Tests for a Temporary Git Repo

**Files:**
- Create: `tests/scripts/test_land_in_temp_repo.py`
- Modify: `scripts/land.sh`

**Step 1: Write the failing test**

Write an integration-style test that:
- creates a temporary git repository
- creates a fake `main`
- creates a feature branch with multiple commits
- runs `scripts/land.sh`
- verifies the result on `main` is a single squash commit

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/scripts/test_land_in_temp_repo.py -v`
Expected: FAIL because the script cannot yet complete the flow in a temp repo.

**Step 3: Write minimal implementation**

Adjust the land script only as needed to support deterministic execution in a temporary repository test environment.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/scripts/test_land_in_temp_repo.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add scripts/land.sh tests/scripts/test_land_in_temp_repo.py
git commit -m "test: verify squash land flow"
```

### Task 6: Define Repository Strict Validation Commands

**Files:**
- Modify: `scripts/verify-strict.sh`
- Create: `docs/setup/strict-validation.md`

**Step 1: Write the failing test**

Write tests that verify:
- the script includes the repository's default strict validation command list
- command failures stop the script immediately
- command order is deterministic

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/scripts/test_verify_strict.py -v`
Expected: FAIL because the strict validation set is incomplete or undocumented.

**Step 3: Write minimal implementation**

Encode the default validation suite for this repository in `scripts/verify-strict.sh` and document it in `docs/setup/strict-validation.md`.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/scripts/test_verify_strict.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add scripts/verify-strict.sh docs/setup/strict-validation.md
git commit -m "docs: define strict validation gate"
```

### Task 7: Verify End-to-End Symphony Landing Prerequisites

**Files:**
- Create: `docs/verification/symphony-auto-land.md`
- Modify: `docs/setup/symphony.md`

**Step 1: Write the failing test**

Write a checklist test or manual verification spec that covers:
- Symphony can read the updated `WORKFLOW.md`
- `scripts/verify-strict.sh` can run in a workspace
- `scripts/land.sh` can land a prepared branch in a safe test repo
- `Done` is only valid after push success

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/scripts -v`
Expected: FAIL or incomplete coverage until the land flow is fully wired.

**Step 3: Write minimal implementation**

Add verification docs describing how to validate the end-to-end land workflow safely before relying on it in production issue handling.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/scripts -v`
Expected: PASS

**Step 5: Commit**

```bash
git add docs/verification/symphony-auto-land.md docs/setup/symphony.md tests/scripts
git commit -m "test: add symphony auto-land verification"
```

## Notes

- This plan intentionally avoids implementing pull request flows; the approved landing mode is direct squash merge to `main`.
- The land flow must never close a Linear issue before push succeeds.
- Network, auth, and proxy failures must be treated as blockers, not silent fallbacks, during landing.
