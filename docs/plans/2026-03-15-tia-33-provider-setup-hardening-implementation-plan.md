# TIA-33 Provider Setup Hardening Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Harden CLI provider setup checks so `doctor`, translation, and voice commands report actionable OCR, translation, TTS, and media-tooling prerequisites.

**Architecture:** Keep validation close to the existing provider boundaries instead of introducing a new config system. Extend `doctor` to exercise the real setup checks used by OCR, translation, and TTS, then add command-level handling where provider initialization errors are not currently surfaced cleanly.

**Tech Stack:** Python, Typer, pytest

---

### Task 1: Lock the New Validation Behavior with Tests

**Files:**
- Modify: `apps/cli/tests/test_new_command.py`
- Modify: `apps/cli/tests/test_translation_service.py`
- Modify: `apps/cli/tests/test_voice_generation.py`
- Modify: `tests/docs/test_setup_docs.py`

**Step 1: Write the failing test**

Add tests that verify:
- `doctor` checks media tooling plus OCR, translation, and TTS setup using the real provider prerequisites
- `doctor` prints actionable messages for missing env vars and unsupported provider config
- `voice` surfaces TTS provider setup failures cleanly
- setup docs mention the required env vars, package/import checks, and `doctor`

**Step 2: Run test to verify it fails**

Run: `python -m pytest apps/cli/tests/test_new_command.py apps/cli/tests/test_translation_service.py apps/cli/tests/test_voice_generation.py tests/docs/test_setup_docs.py -v`
Expected: FAIL because `doctor` only checks executables, OCR checks the wrong dependency, and `voice` does not explicitly handle provider setup errors.

**Step 3: Write minimal implementation**

Implement only the setup-validation changes needed to satisfy the new tests.

**Step 4: Run test to verify it passes**

Run: `python -m pytest apps/cli/tests/test_new_command.py apps/cli/tests/test_translation_service.py apps/cli/tests/test_voice_generation.py tests/docs/test_setup_docs.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add apps/cli/tests/test_new_command.py apps/cli/tests/test_translation_service.py apps/cli/tests/test_voice_generation.py tests/docs/test_setup_docs.py
git commit -m "test: cover provider setup validation"
```

### Task 2: Implement Provider and Doctor Validation

**Files:**
- Modify: `apps/cli/app/commands/doctor.py`
- Modify: `apps/cli/app/commands/voice.py`
- Modify: `apps/cli/app/services/ocr_service.py`
- Modify: `apps/cli/app/services/translation_service.py`
- Modify: `apps/api/app/integrations/moyin_tts.py`

**Step 1: Write the failing test**

Use the task 1 failures as the specification for:
- OCR import validation
- translation provider configuration validation
- TTS provider configuration validation
- clean command error reporting

**Step 2: Run test to verify it fails**

Run: `python -m pytest apps/cli/tests/test_new_command.py apps/cli/tests/test_translation_service.py apps/cli/tests/test_voice_generation.py -v`
Expected: FAIL until the new validation hooks and error handling are in place.

**Step 3: Write minimal implementation**

Implement:
- doctor checks grouped around media tooling, OCR, translation, and TTS
- reusable OCR setup validation that checks the actual Python package prerequisite
- explicit translation and TTS setup validation helpers with actionable messages
- `voice` command handling for provider setup errors

**Step 4: Run test to verify it passes**

Run: `python -m pytest apps/cli/tests/test_new_command.py apps/cli/tests/test_translation_service.py apps/cli/tests/test_voice_generation.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add apps/cli/app/commands/doctor.py apps/cli/app/commands/voice.py apps/cli/app/services/ocr_service.py apps/cli/app/services/translation_service.py apps/api/app/integrations/moyin_tts.py
git commit -m "feat: harden provider setup checks"
```

### Task 3: Align Setup Docs with Runtime Checks

**Files:**
- Modify: `README.md`
- Modify: `docs/setup/local-development.md`
- Modify: `docs/setup/mangaocr.md`
- Modify: `docs/setup/translation-env.md`
- Modify: `docs/setup/moyin-env.md`

**Step 1: Write the failing test**

Use the task 1 docs assertions as the specification for the required setup content.

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/docs/test_setup_docs.py -v`
Expected: FAIL until the docs mention the actual dependency and validation workflow.

**Step 3: Write minimal implementation**

Document:
- how `doctor` validates setup
- the `manga_ocr` import requirement for OCR
- translation provider env requirements
- TTS env requirements
- media tooling expectations

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/docs/test_setup_docs.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add README.md docs/setup/local-development.md docs/setup/mangaocr.md docs/setup/translation-env.md docs/setup/moyin-env.md
git commit -m "docs: align provider setup guidance"
```
