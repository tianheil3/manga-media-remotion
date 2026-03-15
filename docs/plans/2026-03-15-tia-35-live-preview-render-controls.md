# TIA-35 Live Preview Render Controls Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Wire the running web review app so the mounted preview page can trigger a preview render, poll job status, and show terminal render outcomes with usable output details.

**Architecture:** Keep the existing render-job client helpers intact and add a thin state/action layer in the mounted React app. `App` should own the active preview job state and pass a render action into `PreviewPage`, while `PreviewPage` remains responsible for presenting render status and invoking the action. Reuse the FastAPI-provided `outputFile` URL directly so the UI exposes the same artifact path returned by the backend.

**Tech Stack:** React, TypeScript, Node test runner, FastAPI render job API

---

### Task 1: Add a failing mounted-app preview render test

**Files:**
- Modify: `apps/web/tests/project-overview.test.tsx`
- Modify: `apps/web/src/App.tsx`
- Modify: `apps/web/src/pages/PreviewPage.tsx`

**Step 1: Write the failing test**

Add a test that renders `App`, finds the preview button, calls its click handler, and asserts that:

- `api.createRenderJob()` is called with `{ kind: "preview" }`
- `api.getRenderJob()` is polled until completion
- preview render status moves through queued/running/completed
- the completed output URL is rendered for the user

```tsx
test("mounted app can trigger preview renders and expose the completed artifact url", async () => {
  const updates = [
    { id: "render-preview-010", status: "running", outputFile: "/projects/demo-001/media/renders/preview.mp4" },
    { id: "render-preview-010", status: "completed", outputFile: "/projects/demo-001/media/renders/preview.mp4" },
  ];
  const api = {
    createRenderJob: async () => ({
      id: "render-preview-010",
      projectId: "demo-001",
      kind: "preview",
      status: "queued",
      outputFile: "/projects/demo-001/media/renders/preview.mp4",
      createdAt: "2026-03-15T00:00:00.000Z",
      updatedAt: "2026-03-15T00:00:00.000Z",
      statusPath: "/projects/demo-001/render-jobs/render-preview-010",
    }),
    getRenderJob: async () => updates.shift(),
  };

  const tree = App({ api, projectId: "demo-001", project, scenes, activeJob: null });
  const button = findElement(tree, (node) => node.type === "button" && node.props.children === "Trigger preview render");

  await button.props.onClick();

  const rerendered = App({ api, projectId: "demo-001", project, scenes, activeJob: null });
  assert.match(renderToStaticMarkup(rerendered), /Preview render completed\./);
  assert.match(renderToStaticMarkup(rerendered), /\/projects\/demo-001\/media\/renders\/preview\.mp4/);
});
```

**Step 2: Run test to verify it fails**

Run: `node --import ./tools/register-tsx.mjs --test apps/web/tests/project-overview.test.tsx`

Expected: FAIL because the preview button has no mounted click action and the app does not preserve active render job state.

**Step 3: Write minimal implementation**

Add preview render state to `App`, build preview actions next to the existing review actions, and pass them into `PreviewPage`. Keep polling in the existing workflow helper.

**Step 4: Run test to verify it passes**

Run: `node --import ./tools/register-tsx.mjs --test apps/web/tests/project-overview.test.tsx`

Expected: PASS

**Step 5: Commit**

```bash
git add docs/plans/2026-03-15-tia-35-live-preview-render-controls.md apps/web/tests/project-overview.test.tsx apps/web/src/App.tsx apps/web/src/pages/PreviewPage.tsx
git commit -m "feat: wire preview render controls in web app"
```

### Task 2: Surface render outcome details in the preview UI

**Files:**
- Modify: `apps/web/src/pages/PreviewPage.tsx`
- Modify: `apps/web/src/lib/workflow.ts`
- Modify: `apps/web/tests/project-overview.test.tsx`
- Modify: `apps/web/tests/workflow.test.ts`

**Step 1: Write the failing test**

Add assertions that completed renders expose the artifact URL and failed renders expose the persisted error text while keeping the trigger button re-enabled for terminal jobs.

```tsx
assert.match(markup, /Preview render completed\./);
assert.match(markup, /Open render artifact/);
assert.match(markup, /Missing script\/scenes\.json for render job\./);
```

**Step 2: Run test to verify it fails**

Run: `npm test --workspace apps/web`

Expected: FAIL because the preview page currently renders only a status line and no artifact/error detail block.

**Step 3: Write minimal implementation**

Extend the preview state/view model so `PreviewPage` can render:

- queued/running/completed/failed notices
- a clickable artifact URL on completion
- the persisted `errorMessage` on failure

Do not add extra render kinds or broader workflow changes.

**Step 4: Run test to verify it passes**

Run: `npm test --workspace apps/web`

Expected: PASS

**Step 5: Commit**

```bash
git add apps/web/src/pages/PreviewPage.tsx apps/web/src/lib/workflow.ts apps/web/tests/project-overview.test.tsx apps/web/tests/workflow.test.ts
git commit -m "feat: expose preview render outcomes"
```

### Task 3: Re-run required validation and update Linear

**Files:**
- Modify: `apps/web/tests/project-overview.test.tsx`
- Modify: `apps/web/src/App.tsx`
- Modify: `apps/web/src/pages/PreviewPage.tsx`
- Modify: `apps/web/src/lib/workflow.ts`

**Step 1: Run required validation**

Run: `npm test --workspace apps/web`

Expected: PASS

**Step 2: Run required API validation**

Run: `python -m pytest apps/api/tests/test_render_api.py -v`

Expected: PASS

**Step 3: Update the Linear workpad**

Record implementation notes, final validation output, and any residual risks in the existing `## Codex Workpad` comment.

**Step 4: Commit**

```bash
git status --short
```

Expected: only the intended issue files remain changed after validation.
