# TIA-21 Voice Duration Sync Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Persist real voice audio durations and keep scene review data synchronized when voice audio is generated, replaced, or skipped.

**Architecture:** Measure WAV durations in the Python orchestration layer when audio files are written, persist those values onto `voices.json`, and have scene generation and voice-update flows synchronize `scenes.json` using a stable voice reference. Keep the web layer thin by consuming the normalized API payload instead of recomputing sync rules in React.

**Tech Stack:** Python, FastAPI, Pydantic, React, TypeScript, Node.js

---

### Task 1: Lock Down Duration Persistence With Failing Tests

**Files:**
- Modify: `apps/cli/tests/test_voice_generation.py`
- Modify: `apps/cli/tests/test_recording_flow.py`
- Test: `apps/cli/tests/test_voice_generation.py`
- Test: `apps/cli/tests/test_recording_flow.py`

**Step 1: Write the failing test**

Add coverage that uses valid WAV fixtures so:
- generated TTS segments persist a positive `durationMs`
- replaced recordings overwrite `durationMs`
- skipped recordings clear audio linkage and duration

**Step 2: Run test to verify it fails**

Run: `python -m pytest apps/cli/tests/test_voice_generation.py apps/cli/tests/test_recording_flow.py -q`
Expected: FAIL because audio durations are currently not measured or updated.

**Step 3: Write minimal implementation**

Add a small WAV duration helper and apply it when saving generated or recorded audio. Ensure skip clears stale audio timing state.

**Step 4: Run test to verify it passes**

Run: `python -m pytest apps/cli/tests/test_voice_generation.py apps/cli/tests/test_recording_flow.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add apps/cli
git commit -m "fix: persist measured voice durations"
```

### Task 2: Lock Down Scene Sync and Rebuild Behavior

**Files:**
- Modify: `apps/cli/tests/test_scene_builder.py`
- Modify: `apps/api/tests/test_voice_api.py`
- Modify: `apps/web/tests/scene-review-model.test.ts`
- Test: `apps/cli/tests/test_scene_builder.py`
- Test: `apps/api/tests/test_voice_api.py`
- Test: `apps/web/tests/scene-review-model.test.ts`

**Step 1: Write the failing test**

Add coverage that verifies:
- voiced scenes use measured durations plus padding
- skipped voices rebuild to a no-audio scene without `0 + padding`
- replacing or skipping a voice updates scene review preview audio and metadata together

**Step 2: Run test to verify it fails**

Run: `python -m pytest apps/cli/tests/test_scene_builder.py apps/api/tests/test_voice_api.py -q`
Expected: FAIL because scenes are keyed by stale audio paths and use missing durations incorrectly.

Run: `npm test --workspace apps/web -- scene-review-model.test.ts`
Expected: May be blocked by missing local dependencies; record the exact output if so.

**Step 3: Write minimal implementation**

Persist a stable `voiceId` on voiced scenes, update scene synchronization in the Python layer when voice assets change, and expose synced metadata to the scene-review model.

**Step 4: Run test to verify it passes**

Run: `python -m pytest apps/cli/tests/test_scene_builder.py apps/api/tests/test_voice_api.py -q`
Expected: PASS

Run: `npm test --workspace apps/web -- scene-review-model.test.ts`
Expected: PASS if local dependencies are available.

**Step 5: Commit**

```bash
git add apps/api apps/cli apps/web packages/schema
git commit -m "fix: keep scene audio references in sync"
```

### Task 3: Verify Ticket Acceptance End To End

**Files:**
- Modify: `apps/api/app/routes/voice.py`
- Modify: `apps/cli/app/services/scene_builder.py`
- Modify: `apps/cli/app/services/recording.py`
- Modify: `apps/cli/app/services/voice_generation.py`
- Modify: `apps/api/app/models/scene.py`
- Modify: `packages/schema/src/scene.ts`
- Modify: `packages/schema/src/api.ts`

**Step 1: Run focused validation**

Run:
- `python -m pytest apps/cli/tests/test_voice_generation.py apps/cli/tests/test_recording_flow.py apps/cli/tests/test_scene_builder.py apps/api/tests/test_voice_api.py -q`
- `npm test --workspace apps/web -- scene-review-model.test.ts scene-review.test.tsx`

Expected:
- Python tests PASS
- Web tests PASS if dependencies are present; otherwise capture the environment blocker

**Step 2: Run broader regression checks**

Run:
- `python -m pytest apps/api/tests/test_projects_api.py -q`
- `python -m pytest apps/api/tests/test_file_store.py -q`

Expected: PASS

**Step 3: Update tracking**

Update the Linear `## Codex Workpad` comment with:
- sync result
- failing-test and passing-test evidence
- remaining blockers or residual risks

**Step 4: Commit**

```bash
git add docs/plans/2026-03-15-tia-21-voice-duration-sync-implementation-plan.md
git commit -m "docs: add TIA-21 implementation plan"
```
