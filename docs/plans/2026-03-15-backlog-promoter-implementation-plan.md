# Backlog Promoter Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a repository-managed backlog promoter that moves configured Linear issues from `Backlog` to `Todo` after all configured prerequisite issues are `Done`.

**Architecture:** Use a repo-committed JSON config file plus a standalone Python script under `scripts/` so the promoter can run independently of Symphony. Resolve project and state IDs dynamically from Linear at runtime, validate the dependency graph before writes, and support both one-shot and polling execution.

**Tech Stack:** Python 3.12+, JSON, urllib, Linear GraphQL API, pytest

---

### Task 1: Add a Checked-In Promotion Config

**Files:**
- Create: `config/backlog-promoter.json`
- Test: `tests/scripts/test_backlog_promoter.py`

**Step 1: Write the failing test**

Add a test that loads the checked-in config file and asserts:
- `version == 1`
- `sourceState == "Backlog"`
- `targetState == "Todo"`
- `promotions` is non-empty
- every promotion contains `issue` and `dependsOn`

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/scripts/test_backlog_promoter.py -k checked_in_config -v`
Expected: FAIL because the config file and test do not exist yet.

**Step 3: Write minimal implementation**

Create `config/backlog-promoter.json` with:
- project slug
- team key
- source and target state names
- the initial dependency chain for `TIA-34` through `TIA-42`

Keep the first config explicit rather than deriving relationships.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/scripts/test_backlog_promoter.py -k checked_in_config -v`
Expected: PASS

**Step 5: Commit**

```bash
git add config/backlog-promoter.json tests/scripts/test_backlog_promoter.py
git commit -m "test: add backlog promoter config coverage"
```

### Task 2: Build Config Parsing and Validation

**Files:**
- Create: `scripts/backlog-promoter.py`
- Modify: `tests/scripts/test_backlog_promoter.py`

**Step 1: Write the failing test**

Add tests that verify the promoter rejects:
- duplicate target issues
- self-dependencies
- duplicate dependencies inside one rule
- cycles across rules

Use temporary config files in the tests.

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/scripts/test_backlog_promoter.py -k config_validation -v`
Expected: FAIL because config validation logic does not exist yet.

**Step 3: Write minimal implementation**

Implement in `scripts/backlog-promoter.py`:
- config loading from JSON
- basic schema validation
- dependency graph validation
- cycle detection

Expose a small internal API that tests can call indirectly via subprocess or direct helper functions.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/scripts/test_backlog_promoter.py -k config_validation -v`
Expected: PASS

**Step 5: Commit**

```bash
git add scripts/backlog-promoter.py tests/scripts/test_backlog_promoter.py
git commit -m "feat: validate backlog promoter config"
```

### Task 3: Add Linear Read Support and Eligibility Evaluation

**Files:**
- Modify: `scripts/backlog-promoter.py`
- Modify: `tests/scripts/test_backlog_promoter.py`

**Step 1: Write the failing test**

Add tests that verify:
- issues are eligible only when all dependencies are `Done`
- issues not in the configured source state are skipped
- multiple independent issues can be eligible in a single run

Model Linear responses with fake API payloads or mocked HTTP responses.

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/scripts/test_backlog_promoter.py -k eligibility -v`
Expected: FAIL because issue evaluation logic does not exist yet.

**Step 3: Write minimal implementation**

Implement:
- project lookup by slug
- team state lookup by name
- issue lookup by identifier
- eligibility evaluation against the configured dependency list

Keep writes out of scope for this task.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/scripts/test_backlog_promoter.py -k eligibility -v`
Expected: PASS

**Step 5: Commit**

```bash
git add scripts/backlog-promoter.py tests/scripts/test_backlog_promoter.py
git commit -m "feat: evaluate backlog promotion eligibility"
```

### Task 4: Implement Promotion and Dry-Run Behavior

**Files:**
- Modify: `scripts/backlog-promoter.py`
- Modify: `tests/scripts/test_backlog_promoter.py`

**Step 1: Write the failing test**

Add tests that verify:
- eligible issues are updated from `Backlog` to `Todo`
- dry-run logs intended promotions without updating Linear
- one failed update does not block other eligible promotions in the same run

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/scripts/test_backlog_promoter.py -k promotion -v`
Expected: FAIL because promotion writes and dry-run handling are missing.

**Step 3: Write minimal implementation**

Implement:
- Linear issue state update mutation
- dry-run mode
- structured console output for promoted and skipped issues
- per-issue error handling that allows the run to continue

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/scripts/test_backlog_promoter.py -k promotion -v`
Expected: PASS

**Step 5: Commit**

```bash
git add scripts/backlog-promoter.py tests/scripts/test_backlog_promoter.py
git commit -m "feat: add backlog promotion updates"
```

### Task 5: Add One-Shot and Polling CLI Modes

**Files:**
- Modify: `scripts/backlog-promoter.py`
- Modify: `tests/scripts/test_backlog_promoter.py`

**Step 1: Write the failing test**

Add tests that verify:
- `--once` performs a single evaluation pass
- `--dry-run` works with `--once`
- polling mode sleeps between runs
- invalid argument combinations fail with a clear message

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/scripts/test_backlog_promoter.py -k cli_modes -v`
Expected: FAIL because the CLI modes are not implemented.

**Step 3: Write minimal implementation**

Add CLI support for:
- `--once`
- `--poll`
- `--interval-seconds`
- `--dry-run`
- optional config-path override

Keep the default behavior conservative and explicit.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/scripts/test_backlog_promoter.py -k cli_modes -v`
Expected: PASS

**Step 5: Commit**

```bash
git add scripts/backlog-promoter.py tests/scripts/test_backlog_promoter.py
git commit -m "feat: add backlog promoter cli modes"
```

### Task 6: Document Setup and Operating Instructions

**Files:**
- Modify: `docs/setup/symphony.md`
- Create: `docs/setup/backlog-promoter.md`
- Modify: `tests/docs/test_setup_docs.py`

**Step 1: Write the failing test**

Add docs tests asserting:
- `docs/setup/symphony.md` points to the backlog promoter setup doc
- the new doc references the config file, `LINEAR_API_KEY`, and one-shot plus polling commands

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/docs/test_setup_docs.py -v`
Expected: FAIL because the docs do not mention the promoter yet.

**Step 3: Write minimal implementation**

Document:
- the purpose of the promoter
- required environment variables
- config file path
- dry-run usage
- polling usage
- safe rollout guidance

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/docs/test_setup_docs.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add docs/setup/symphony.md docs/setup/backlog-promoter.md tests/docs/test_setup_docs.py
git commit -m "docs: add backlog promoter setup guide"
```

### Task 7: Verify the Full Promoter Path

**Files:**
- Modify: `tests/scripts/test_backlog_promoter.py`
- Modify: `config/backlog-promoter.json` if needed for fixture clarity

**Step 1: Write the failing test**

Add an end-to-end script test that:
- loads a small temp config
- simulates a Linear project with mixed issue states
- runs the promoter once
- verifies only eligible backlog issues are promoted

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/scripts/test_backlog_promoter.py -k end_to_end -v`
Expected: FAIL because the combined path is not fully exercised yet.

**Step 3: Write minimal implementation**

Add any final glue required so the end-to-end one-shot path works without special test-only branches.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/scripts/test_backlog_promoter.py -k end_to_end -v`
Expected: PASS

**Step 5: Run final verification**

Run: `python -m pytest tests/scripts/test_backlog_promoter.py tests/docs/test_setup_docs.py -v`
Expected: PASS

Run: `bash scripts/verify-strict.sh`
Expected: PASS

**Step 6: Commit**

```bash
git add config/backlog-promoter.json scripts/backlog-promoter.py tests/scripts/test_backlog_promoter.py docs/setup/backlog-promoter.md docs/setup/symphony.md tests/docs/test_setup_docs.py
git commit -m "feat: add linear backlog promoter"
```
