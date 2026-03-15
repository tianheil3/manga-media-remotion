# Translation Provider Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the passthrough translation stage with an env-configured DeepL-backed provider while preserving override precedence and preventing partial script corruption on provider failure.

**Architecture:** Keep the existing CLI translation boundary intact by preserving the `TranslationService` protocol and swapping the default implementation behind `get_translation_service()`. Translate script entries fully in memory, then persist `script.json` only after every entry succeeds so failed provider calls do not corrupt prior project data.

**Tech Stack:** Python, Typer, Pydantic, urllib, pytest

---

### Task 1: Lock Required Translation Behavior with Tests

**Files:**
- Modify: `apps/cli/tests/test_script_builder.py`
- Create: `apps/cli/tests/test_translation_service.py`

**Step 1: Write the failing test**

Add tests that verify:
- `translatedText` override wins over provider output while `voiceText` and `subtitleText` remain independently overridable
- provider failure exits the CLI with a bubble-specific error and leaves an existing `script/script.json` untouched
- env-backed provider loading succeeds when DeepL vars are set and fails with an actionable error when they are missing

**Step 2: Run test to verify it fails**

Run: `python -m pytest apps/cli/tests/test_script_builder.py apps/cli/tests/test_translation_service.py -v`
Expected: FAIL because the current implementation still returns `PassthroughTranslationService`, does not load env config, and does not wrap provider errors with actionable context.

**Step 3: Write minimal implementation**

Implement only the smallest translation provider and error-handling changes needed to satisfy the new tests.

**Step 4: Run test to verify it passes**

Run: `python -m pytest apps/cli/tests/test_script_builder.py apps/cli/tests/test_translation_service.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add apps/cli/tests/test_script_builder.py apps/cli/tests/test_translation_service.py
git commit -m "test: cover translation provider behavior"
```

### Task 2: Implement the DeepL-backed Translation Service

**Files:**
- Modify: `apps/cli/app/services/translation_service.py`
- Modify: `apps/cli/app/services/script_builder.py`
- Modify: `apps/cli/app/commands/translate.py`

**Step 1: Write the failing test**

Use the task 1 tests as the failing specification for:
- env-backed provider selection
- actionable provider failure messaging
- failure-safe script persistence

**Step 2: Run test to verify it fails**

Run: `python -m pytest apps/cli/tests/test_script_builder.py apps/cli/tests/test_translation_service.py -v`
Expected: FAIL because production code has not been updated yet.

**Step 3: Write minimal implementation**

Implement:
- `TranslationServiceError`
- `DeepLTranslationService` with `from_env()` and injected transport support
- `get_translation_service()` factory using `TRANSLATION_PROVIDER`
- provider failure wrapping in `build_script_entries()`
- command-level error handling that surfaces configuration and provider failures cleanly

**Step 4: Run test to verify it passes**

Run: `python -m pytest apps/cli/tests/test_script_builder.py apps/cli/tests/test_translation_service.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add apps/cli/app/services/translation_service.py apps/cli/app/services/script_builder.py apps/cli/app/commands/translate.py
git commit -m "feat: add deepl-backed translation provider"
```

### Task 3: Verify the Translation Stage Against the Existing CLI Suite

**Files:**
- Modify: `apps/cli/tests/test_script_builder.py`

**Step 1: Write the failing test**

Ensure the existing translation command coverage still reflects the accepted behavior after the provider change.

**Step 2: Run test to verify it fails**

Run: `python -m pytest apps/cli/tests/test_script_builder.py -v`
Expected: FAIL only if the new provider wiring breaks the existing translation-layer contract.

**Step 3: Write minimal implementation**

Adjust only the minimal test fixtures or assertions needed to reflect the new provider-backed translation path without changing accepted script output semantics.

**Step 4: Run test to verify it passes**

Run: `python -m pytest apps/cli/tests/test_script_builder.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add apps/cli/tests/test_script_builder.py
git commit -m "test: confirm translation command contract"
```
