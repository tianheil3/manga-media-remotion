# Project Integrity Checks And Recovery Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add project integrity detection, a minimal repair command, and targeted CLI/API error surfacing for inconsistent workspace state.

**Architecture:** Introduce a shared Python integrity service that can run a full operator-facing scan or a narrower caller-specific validation. Keep repair deterministic by recreating missing metadata files and resyncing scenes from the current voice state instead of inventing new workflow data.

**Tech Stack:** Python, Typer, FastAPI, Pydantic, pytest

---

### Task 1: Add failing integrity detection tests

**Files:**
- Create: `apps/cli/tests/test_project_integrity.py`
- Modify: `apps/api/tests/test_projects_api.py`
- Modify: `apps/api/tests/test_voice_api.py`

**Step 1: Write the failing test**

Add tests that prove:

- the new CLI integrity command reports missing files, missing media, and broken scene or voice references
- the existing API paths now surface actionable integrity failures instead of returning empty results for missing required files
- legacy scene-review behavior without `voiceId` still works when scenes can still be resolved

**Step 2: Run test to verify it fails**

Run:

- `python -m pytest apps/cli/tests/test_project_integrity.py apps/api/tests/test_projects_api.py apps/api/tests/test_voice_api.py -v`

Expected:

- FAIL because the integrity service and new command paths do not exist yet

**Step 3: Write minimal implementation**

Add only the smallest production hooks needed for those tests to start exercising the new paths.

**Step 4: Run test to verify it passes**

Run:

- `python -m pytest apps/cli/tests/test_project_integrity.py apps/api/tests/test_projects_api.py apps/api/tests/test_voice_api.py -v`

Expected:

- PASS

**Step 5: Commit**

```bash
git add apps/cli/tests/test_project_integrity.py apps/api/tests/test_projects_api.py apps/api/tests/test_voice_api.py
git commit -m "test: add project integrity coverage"
```

### Task 2: Add failing repair tests

**Files:**
- Modify: `apps/cli/tests/test_project_integrity.py`

**Step 1: Write the failing test**

Add tests that prove:

- the repair command recreates missing `config.json`
- the repair command recreates missing `script/voices.json` and `script/scenes.json`
- the repair command resyncs stale scene voice links when voices still exist
- unrepaired missing media is still reported after repair

**Step 2: Run test to verify it fails**

Run:

- `python -m pytest apps/cli/tests/test_project_integrity.py -v`

Expected:

- FAIL because repair behavior is not implemented yet

**Step 3: Write minimal implementation**

Implement deterministic repair helpers and wire them into the new CLI command.

**Step 4: Run test to verify it passes**

Run:

- `python -m pytest apps/cli/tests/test_project_integrity.py -v`

Expected:

- PASS

**Step 5: Commit**

```bash
git add apps/cli/tests/test_project_integrity.py
git commit -m "test: cover project repair behavior"
```

### Task 3: Implement shared integrity service and CLI commands

**Files:**
- Create: `apps/api/app/services/project_integrity.py`
- Create: `apps/cli/app/commands/integrity.py`
- Modify: `apps/cli/app/main.py`

**Step 1: Write the failing test**

Use the tests from Tasks 1 and 2.

**Step 2: Run test to verify it fails**

Run:

- `python -m pytest apps/cli/tests/test_project_integrity.py apps/api/tests/test_projects_api.py apps/api/tests/test_voice_api.py -v`

Expected:

- FAIL against the missing service and command registration

**Step 3: Write minimal implementation**

Implement:

- integrity issue/report models
- full and caller-scoped validation helpers
- human-readable report formatting
- CLI `integrity` and `repair` commands

**Step 4: Run test to verify it passes**

Run:

- `python -m pytest apps/cli/tests/test_project_integrity.py apps/api/tests/test_projects_api.py apps/api/tests/test_voice_api.py -v`

Expected:

- PASS

**Step 5: Commit**

```bash
git add apps/api/app/services/project_integrity.py apps/cli/app/commands/integrity.py apps/cli/app/main.py
git commit -m "feat: add project integrity commands"
```

### Task 4: Integrate targeted integrity surfacing into existing paths

**Files:**
- Modify: `apps/cli/app/commands/run.py`
- Modify: `apps/api/app/routes/projects.py`
- Modify: `apps/api/app/routes/review.py`
- Modify: `apps/api/app/routes/scenes.py`
- Modify: `apps/api/app/routes/voice.py`

**Step 1: Write the failing test**

Use the API and CLI tests from Task 1 to prove missing files no longer silently degrade.

**Step 2: Run test to verify it fails**

Run:

- `python -m pytest apps/cli/tests/test_project_integrity.py apps/api/tests/test_projects_api.py apps/api/tests/test_voice_api.py -v`

Expected:

- FAIL until the routes and CLI command stop swallowing inconsistent state

**Step 3: Write minimal implementation**

Validate only the files and references each caller needs, return actionable errors, and preserve legacy scene-review compatibility.

**Step 4: Run test to verify it passes**

Run:

- `python -m pytest apps/cli/tests/test_project_integrity.py apps/api/tests/test_projects_api.py apps/api/tests/test_voice_api.py -v`

Expected:

- PASS

**Step 5: Commit**

```bash
git add apps/cli/app/commands/run.py apps/api/app/routes/projects.py apps/api/app/routes/review.py apps/api/app/routes/scenes.py apps/api/app/routes/voice.py
git commit -m "feat: surface project integrity errors"
```

### Task 5: Run full validation and update tracking

**Files:**
- Modify: Linear `## Codex Workpad` comment

**Step 1: Run required validation**

Run:

- `python -m pytest apps/cli/tests apps/api/tests -v`

Expected:

- PASS

**Step 2: Record evidence**

Update the Linear `## Codex Workpad` comment with:

- sync and baseline evidence
- failing-test and passing-test evidence
- repair coverage added
- final validation result
- any residual risks
