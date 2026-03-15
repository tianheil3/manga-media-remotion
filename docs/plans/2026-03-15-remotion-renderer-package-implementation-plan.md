# Remotion Renderer Package Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make `apps/remotion` runnable through a stable render CLI and route API render jobs through that package.

**Architecture:** Keep `apps/remotion` responsible for validating render inputs, building composition data, and writing deterministic render artifacts. Keep the Python API layer responsible for job persistence and shelling into the renderer package through a stable CLI contract.

**Tech Stack:** TypeScript, node:test, custom TS loader in `tools/`, Python, FastAPI, subprocess

---

### Task 1: Lock the renderer package contract with failing tests

**Files:**
- Create: `apps/remotion/tests/render-project.test.ts`
- Modify: `apps/api/tests/test_render_api.py`

**Step 1: Write the failing test**

Add a remotion package test that expects a renderer entrypoint to read `project.json` and `script/scenes.json`, write a deterministic artifact, and expose help output. Update the API render-job test to expect a renderer-owned artifact marker instead of the old placeholder text file.

**Step 2: Run test to verify it fails**

Run: `npm test --workspace apps/remotion`
Expected: FAIL because the renderer entrypoint does not exist.

Run: `python -m pytest apps/api/tests/test_render_api.py -v`
Expected: FAIL because the API still writes placeholder artifacts itself.

**Step 3: Write minimal implementation**

Add the renderer module, CLI contract, and enough API integration to satisfy the new assertions.

**Step 4: Run test to verify it passes**

Run: `npm test --workspace apps/remotion`
Expected: PASS

Run: `python -m pytest apps/api/tests/test_render_api.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add apps/remotion apps/api docs/plans
git commit -m "feat: add runnable remotion renderer package"
```

### Task 2: Add runtime scripts and contract docs

**Files:**
- Modify: `apps/remotion/package.json`
- Create: `apps/remotion/README.md`

**Step 1: Write the failing test**

Use the existing validation command as the failure signal:

Run: `npm run render --workspace apps/remotion -- --help`
Expected: FAIL with `Missing script: "render"`.

**Step 2: Run test to verify it fails**

The current baseline already shows this failure.

**Step 3: Write minimal implementation**

Add `render`, `render:preview`, and `render:final` scripts and document the API-facing CLI contract in `apps/remotion/README.md`.

**Step 4: Run test to verify it passes**

Run: `npm run render --workspace apps/remotion -- --help`
Expected: PASS and print the supported CLI flags.

**Step 5: Commit**

```bash
git add apps/remotion/package.json apps/remotion/README.md
git commit -m "docs: add remotion renderer contract"
```
