# Review Pages Editable Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make the frame-review and scene-review web pages support local edits, validation, save flows, response-driven draft refresh, and visible loading/saving/error state.

**Architecture:** Keep the existing file-backed API contract unchanged. Add page-level review state helpers in `apps/web` that manage editable drafts, validation errors, async save state, and refresh the draft from the saved API response so the UI always reflects server-backed data.

**Tech Stack:** TypeScript, node:test, React-style page render functions in `apps/web`, existing FastAPI review endpoints

---

### Task 1: Add Frame Review Page State Tests

**Files:**
- Modify: `apps/web/tests/frame-review.test.tsx`
- Modify: `apps/web/src/pages/FrameReviewPage.tsx`
- Modify: `apps/web/src/lib/frame-review.ts`

**Step 1: Write the failing test**

Add tests that cover:
- editing `textEdited`, `order`, `kind`, and `speaker`
- blocking save when frame draft validation fails
- save success refreshing the local draft from the API response
- save failure surfacing an error state without losing the draft

**Step 2: Run test to verify it fails**

Run: `node --import ./tools/register-tsx.mjs --test apps/web/tests/frame-review.test.tsx`
Expected: FAIL because the page module does not yet expose editable state, validation, or save lifecycle handling.

**Step 3: Write minimal implementation**

Add frame-review page state helpers and wire the page renderer to the new state shape.

**Step 4: Run test to verify it passes**

Run: `node --import ./tools/register-tsx.mjs --test apps/web/tests/frame-review.test.tsx`
Expected: PASS

### Task 2: Add Scene Review Page State Tests

**Files:**
- Modify: `apps/web/tests/scene-review.test.tsx`
- Modify: `apps/web/src/pages/SceneReviewPage.tsx`
- Modify: `apps/web/src/lib/scene-review.ts`

**Step 1: Write the failing test**

Add tests that cover:
- editing `subtitleText`, `durationMs`, and `stylePreset`
- blocking save when scene draft validation fails
- save success refreshing the local draft from the API response
- save failure surfacing an error state without losing the draft

**Step 2: Run test to verify it fails**

Run: `node --import ./tools/register-tsx.mjs --test apps/web/tests/scene-review.test.tsx`
Expected: FAIL because the page module does not yet expose editable state, validation, or save lifecycle handling.

**Step 3: Write minimal implementation**

Add scene-review page state helpers and wire the page renderer to the new state shape.

**Step 4: Run test to verify it passes**

Run: `node --import ./tools/register-tsx.mjs --test apps/web/tests/scene-review.test.tsx`
Expected: PASS

### Task 3: Targeted Verification

**Files:**
- Modify: `apps/web/tests/frame-review.test.tsx`
- Modify: `apps/web/tests/scene-review.test.tsx`

**Step 1: Run targeted verification**

Run: `node --import ./tools/register-tsx.mjs --test apps/web/tests/frame-review.test.tsx apps/web/tests/scene-review.test.tsx`
Expected: PASS

**Step 2: Record validation**

Update the Linear workpad with the exact commands, results, and any environment constraints still present outside the targeted scope.
