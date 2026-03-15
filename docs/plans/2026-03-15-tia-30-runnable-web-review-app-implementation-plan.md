# TIA-30 Runnable Web Review App Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Turn `apps/web` into a real local review app with runnable `dev` and `build` entrypoints, a browser boot path, configurable API base URL support, and working project loading against the API.

**Architecture:** Keep the existing review shell and API client logic as the source of truth. Add a small browser-specific shell that owns runtime configuration and loading state, mount it with real React DOM, and use Vite for the minimal dev/build pipeline. Stabilize the existing `apps/web` tests where they currently depend on shim limitations or brittle child indexes so the ticket can add new runtime coverage without carrying false negatives.

**Tech Stack:** TypeScript, React 18, React DOM, Vite, node:test

---

### Task 1: Stabilize the Current `apps/web` Test Baseline

**Files:**
- Modify: `apps/web/tests/project-overview.test.tsx`
- Modify: `apps/web/tests/frame-review.test.tsx`
- Modify: `apps/web/tests/scene-review.test.tsx`
- Reference: `apps/web/src/App.tsx`
- Reference: `apps/web/src/pages/FrameReviewPage.tsx`
- Reference: `apps/web/src/pages/SceneReviewPage.tsx`
- Reference: `tools/shims/react-dom-server.mjs`

**Step 1: Write the failing test adjustments**

Update the failing assertions so they cover the same behavior without depending on unsupported hook rendering through the shimmed server renderer or fragile child indexes.

**Step 2: Run test to verify it fails for the expected reason**

Run: `node --import ../../tools/register-tsx.mjs --test apps/web/tests/project-overview.test.tsx apps/web/tests/frame-review.test.tsx apps/web/tests/scene-review.test.tsx`
Expected: FAIL on the currently red assertions before the production changes land.

**Step 3: Write minimal implementation**

Change the tests to:
- render `AppView` when the behavior under test is structural shell composition rather than hook lifecycle
- find page controls by element props and names instead of hard-coded child array offsets

**Step 4: Run test to verify it passes**

Run: `node --import ../../tools/register-tsx.mjs --test apps/web/tests/project-overview.test.tsx apps/web/tests/frame-review.test.tsx apps/web/tests/scene-review.test.tsx`
Expected: PASS

**Step 5: Commit**

```bash
git add apps/web/tests/project-overview.test.tsx apps/web/tests/frame-review.test.tsx apps/web/tests/scene-review.test.tsx
git commit -m "test: stabilize apps web shell tests"
```

### Task 2: Add Failing Coverage for the Runnable Browser App

**Files:**
- Create: `apps/web/tests/browser-entry.test.tsx`
- Create: `apps/web/src/browser/config.ts`
- Create: `apps/web/src/browser/ReviewApp.tsx`
- Create: `apps/web/src/main.tsx`
- Create: `apps/web/index.html`
- Modify: `apps/web/src/lib/api.ts`

**Step 1: Write the failing test**

Write browser-runtime tests that verify:
- runtime config resolves API base URL from env/defaults and explicit user input
- the browser shell loads a project through the existing API client contract
- load failures surface a readable error instead of crashing
- the mounted shell passes project, frame review, scene review, and preview data into the existing review view

**Step 2: Run test to verify it fails**

Run: `node --import ../../tools/register-tsx.mjs --test apps/web/tests/browser-entry.test.tsx`
Expected: FAIL because the browser runtime modules do not exist yet.

**Step 3: Write minimal implementation**

Create the runtime config helpers and browser shell module with the smallest API needed by the new tests. Add the HTML entrypoint and `src/main.tsx` boot file that mounts the shell with React DOM.

**Step 4: Run test to verify it passes**

Run: `node --import ../../tools/register-tsx.mjs --test apps/web/tests/browser-entry.test.tsx`
Expected: PASS

**Step 5: Commit**

```bash
git add apps/web/tests/browser-entry.test.tsx apps/web/src/browser/config.ts apps/web/src/browser/ReviewApp.tsx apps/web/src/main.tsx apps/web/index.html apps/web/src/lib/api.ts
git commit -m "feat: add browser review app shell"
```

### Task 3: Add Real `dev` and `build` Support for `apps/web`

**Files:**
- Modify: `apps/web/package.json`
- Create: `apps/web/vite.config.ts`
- Modify: `package-lock.json`
- Reference: `apps/remotion/src/VideoComposition.tsx`

**Step 1: Write the failing test or command expectation**

Capture the current missing-script baseline for:
- `npm run build --workspace apps/web`
- `npm run dev --workspace apps/web -- --host 127.0.0.1 --strictPort`

**Step 2: Run command to verify it fails**

Run: `npm run build --workspace apps/web`
Expected: FAIL with `Missing script: "build"`

**Step 3: Write minimal implementation**

Add:
- runtime dependencies for real browser execution
- `dev` and `build` scripts for `apps/web`
- a minimal Vite config that serves `apps/web/index.html` and builds the app from the workspace

**Step 4: Run command to verify it passes**

Run: `npm run build --workspace apps/web`
Expected: PASS and emit a browser build under `apps/web/dist`

**Step 5: Commit**

```bash
git add apps/web/package.json apps/web/vite.config.ts package-lock.json
git commit -m "build: add apps web vite runtime"
```

### Task 4: Update Local Setup Docs for the Runnable Review App

**Files:**
- Modify: `docs/setup/local-development.md`
- Modify: `README.md`

**Step 1: Write the failing doc expectation**

Identify the missing local-run instructions for:
- installing the web workspace dependencies
- configuring the API base URL
- starting the API and the web review app together

**Step 2: Verify the gap**

Run: `rg -n "apps/web|VITE_API_BASE_URL|npm run dev --workspace apps/web" docs/setup/local-development.md README.md`
Expected: no runnable `apps/web` guidance today

**Step 3: Write minimal implementation**

Document:
- the required `npm install`
- the new `apps/web` `dev` and `build` commands
- the supported API base URL configuration path
- the minimal local flow for loading a project from `workspace/<project-id>/`

**Step 4: Verify the docs contain the new flow**

Run: `rg -n "apps/web|VITE_API_BASE_URL|npm run dev --workspace apps/web|npm run build --workspace apps/web" docs/setup/local-development.md README.md`
Expected: the new runnable web app instructions are present

**Step 5: Commit**

```bash
git add docs/setup/local-development.md README.md
git commit -m "docs: add runnable web review app setup"
```

### Task 5: Full Validation and Ticket Handoff

**Files:**
- Modify: `apps/web/tests/browser-entry.test.tsx` if validation exposes a missed edge case
- Modify: `apps/web/src/browser/ReviewApp.tsx` only if validation reveals a real runtime gap
- Modify: `apps/web/package.json` only if validation exposes missing build wiring

**Step 1: Run required validation**

Run: `npm test --workspace apps/web`
Expected: PASS

**Step 2: Run required build validation**

Run: `npm run build --workspace apps/web`
Expected: PASS

**Step 3: Fix only real validation regressions**

If anything fails, add or refine the narrowest failing test first, then implement the smallest production change to make it pass.

**Step 4: Re-run validation**

Run: `npm test --workspace apps/web && npm run build --workspace apps/web`
Expected: both commands PASS

**Step 5: Commit**

```bash
git add apps/web docs/setup/local-development.md README.md package-lock.json
git commit -m "feat: finish runnable web review app"
```
