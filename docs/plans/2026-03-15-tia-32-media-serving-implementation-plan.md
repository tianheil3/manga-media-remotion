# TIA-32 Media Serving Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Serve project media and render artifacts through stable API URLs so the running web app can load images, audio, and render outputs directly.

**Architecture:** Add one project-scoped media file route under the FastAPI `/projects` namespace and reuse it when serializing frames, scene review payloads, and render jobs. Keep all files on disk under `workspace/<project-id>/`, validate paths stay inside the project root, and return explicit 404 details when a requested file is missing.

**Tech Stack:** Python, FastAPI, Pydantic, pytest, file-backed project state in `workspace/<project-id>/`

---

### Task 1: Lock the API contract with failing tests

**Files:**
- Modify: `apps/api/tests/test_projects_api.py`
- Modify: `apps/api/tests/test_voice_api.py`
- Modify: `apps/api/tests/test_render_api.py`

**Step 1: Write the failing tests**

Add assertions that:
- frame `image` values become `/projects/<id>/media/...`
- scene `image`, scene `audio`, and `audioMetadata.audioFile` values become `/projects/<id>/media/...`
- render job `outputFile` becomes `/projects/<id>/media/...`
- missing project media requests return a 404 with a specific detail message

**Step 2: Run test to verify it fails**

Run: `python -m pytest apps/api/tests/test_projects_api.py apps/api/tests/test_voice_api.py apps/api/tests/test_render_api.py -v`
Expected: FAIL because API responses still expose project-relative file paths and there is no media-serving route yet.

**Step 3: Commit**

```bash
git add apps/api/tests/test_projects_api.py apps/api/tests/test_voice_api.py apps/api/tests/test_render_api.py
git commit -m "test: define media-serving api contract"
```

### Task 2: Implement project media serving and payload serialization

**Files:**
- Create: `apps/api/app/routes/media.py`
- Modify: `apps/api/app/main.py`
- Modify: `apps/api/app/routes/review.py`
- Modify: `apps/api/app/routes/scenes.py`
- Modify: `apps/api/app/routes/voice.py`
- Modify: `apps/api/app/routes/render.py`

**Step 1: Write the minimal implementation**

Add a `/projects/{project_id}/media/{media_path:path}` endpoint that:
- resolves the project directory from `request.app.state.workspace_root`
- rejects paths that escape the project directory
- returns `FileResponse` for existing files
- returns a 404 with a concrete `detail` when the file does not exist

Update frame, scene review, scene, and render job payload builders to replace project-relative media paths with the new API URL form while keeping non-media control paths unchanged.

**Step 2: Run test to verify it passes**

Run: `python -m pytest apps/api/tests/test_projects_api.py apps/api/tests/test_voice_api.py apps/api/tests/test_render_api.py -v`
Expected: PASS with media URLs served through the new route and missing files producing actionable 404s.

**Step 3: Commit**

```bash
git add apps/api/app/main.py apps/api/app/routes/media.py apps/api/app/routes/review.py apps/api/app/routes/scenes.py apps/api/app/routes/voice.py apps/api/app/routes/render.py
git commit -m "feat: serve project media through api urls"
```

### Task 3: Run ticket validation and update the workpad

**Files:**
- Modify: Linear `## Codex Workpad` comment

**Step 1: Run required validation**

Run: `python -m pytest apps/api/tests -v`
Expected: PASS.

**Step 2: Record evidence**

Update the Linear `## Codex Workpad` comment with:
- completed checklist items
- sync/baseline evidence
- validation command and result
- any blockers or caveats
