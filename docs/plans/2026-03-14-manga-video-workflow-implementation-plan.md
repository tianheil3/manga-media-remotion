# Manga Video Workflow Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build an MVP that converts manga images into a reviewable short-form video workflow using a Python CLI, FastAPI API, React web review UI, and Remotion renderer.

**Architecture:** Use Python as the orchestration layer for OCR, project state, and audio workflows; use React for review UI; keep Remotion isolated as a renderer that consumes normalized `scenes.json`. Store all project state on disk inside `workspace/<project-id>` so every stage can be resumed and edited without a database.

**Tech Stack:** Python, FastAPI, Typer, Pydantic, MangaOCR, React, TypeScript, Remotion, Zod, Node.js

---

### Task 1: Bootstrap Monorepo Layout

**Files:**
- Create: `apps/cli/`
- Create: `apps/api/`
- Create: `apps/web/`
- Create: `apps/remotion/`
- Create: `packages/schema/`
- Create: `packages/shared/`
- Create: `workspace/.gitkeep`
- Create: `README.md`

**Step 1: Write the failing test**

Create a bootstrap validation script or test that asserts the expected top-level directories exist after setup.

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/bootstrap/test_layout.py -v`
Expected: FAIL because the directories and files do not exist yet.

**Step 3: Write minimal implementation**

Create the directory structure and a small top-level README that explains the app split and local-first workspace model.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/bootstrap/test_layout.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add README.md apps packages workspace tests/bootstrap/test_layout.py
git commit -m "chore: bootstrap manga video workspace"
```

### Task 2: Define Shared Project Schema

**Files:**
- Create: `packages/schema/src/project.ts`
- Create: `packages/schema/src/frame.ts`
- Create: `packages/schema/src/voice.ts`
- Create: `packages/schema/src/scene.ts`
- Create: `packages/schema/src/index.ts`
- Create: `packages/schema/package.json`
- Create: `packages/schema/tests/schema.test.ts`

**Step 1: Write the failing test**

Write schema tests that validate:
- a project file shape
- an OCR frame file shape
- a voice segment file shape
- a scene file shape
- rejection of missing required fields

**Step 2: Run test to verify it fails**

Run: `npm test --workspace packages/schema`
Expected: FAIL because the schema package is not implemented yet.

**Step 3: Write minimal implementation**

Implement Zod schemas and exported types for the on-disk data contracts described in the design doc.

**Step 4: Run test to verify it passes**

Run: `npm test --workspace packages/schema`
Expected: PASS

**Step 5: Commit**

```bash
git add packages/schema
git commit -m "feat: add shared manga video schemas"
```

### Task 3: Add Python Project Models and File Store

**Files:**
- Create: `apps/api/app/models/project.py`
- Create: `apps/api/app/models/frame.py`
- Create: `apps/api/app/models/voice.py`
- Create: `apps/api/app/models/scene.py`
- Create: `apps/api/app/services/file_store.py`
- Create: `apps/api/tests/test_file_store.py`
- Create: `apps/cli/app/models/`

**Step 1: Write the failing test**

Write tests that load and save `project.json`, `frames.json`, `voices.json`, and `scenes.json` into a temporary workspace directory.

**Step 2: Run test to verify it fails**

Run: `python -m pytest apps/api/tests/test_file_store.py -v`
Expected: FAIL because models and file-store helpers do not exist.

**Step 3: Write minimal implementation**

Add Pydantic models mirroring the shared schema and implement file-store helpers for loading and persisting project data.

**Step 4: Run test to verify it passes**

Run: `python -m pytest apps/api/tests/test_file_store.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add apps/api apps/cli
git commit -m "feat: add file-backed project models"
```

### Task 4: Build CLI Project Initialization

**Files:**
- Create: `apps/cli/app/main.py`
- Create: `apps/cli/app/commands/new.py`
- Create: `apps/cli/app/commands/open.py`
- Create: `apps/cli/app/commands/doctor.py`
- Create: `apps/cli/tests/test_new_command.py`

**Step 1: Write the failing test**

Write tests for:
- `new` creates the expected workspace directory and base files
- `open` resolves an existing project
- `doctor` checks required tools and reports missing dependencies

**Step 2: Run test to verify it fails**

Run: `python -m pytest apps/cli/tests/test_new_command.py -v`
Expected: FAIL because the CLI commands do not exist.

**Step 3: Write minimal implementation**

Implement a Typer CLI with the three commands and create the initial workspace structure and project metadata.

**Step 4: Run test to verify it passes**

Run: `python -m pytest apps/cli/tests/test_new_command.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add apps/cli
git commit -m "feat: add project bootstrap cli"
```

### Task 5: Build Image Import Stage

**Files:**
- Create: `apps/cli/app/commands/import_images.py`
- Create: `apps/cli/app/services/image_import.py`
- Create: `apps/cli/tests/test_import_images.py`

**Step 1: Write the failing test**

Write tests that verify:
- images are copied into `workspace/<project-id>/images`
- import order is preserved
- metadata is recorded in project files

**Step 2: Run test to verify it fails**

Run: `python -m pytest apps/cli/tests/test_import_images.py -v`
Expected: FAIL because import code is missing.

**Step 3: Write minimal implementation**

Implement an import command that validates image files, copies them into the workspace, and writes ordered frame stubs.

**Step 4: Run test to verify it passes**

Run: `python -m pytest apps/cli/tests/test_import_images.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add apps/cli
git commit -m "feat: add image import stage"
```

### Task 6: Integrate OCR Stage

**Files:**
- Create: `apps/cli/app/commands/ocr.py`
- Create: `apps/cli/app/services/ocr_service.py`
- Create: `apps/cli/app/services/reading_order.py`
- Create: `apps/cli/tests/test_reading_order.py`
- Create: `apps/cli/tests/test_ocr_command.py`

**Step 1: Write the failing test**

Write tests for:
- manga bubble sorting from right to left, then top to bottom
- OCR stage creates per-image JSON output
- OCR output is connected to imported frames

**Step 2: Run test to verify it fails**

Run: `python -m pytest apps/cli/tests/test_reading_order.py apps/cli/tests/test_ocr_command.py -v`
Expected: FAIL because the OCR and sorting services do not exist.

**Step 3: Write minimal implementation**

Wrap MangaOCR behind a service interface, add deterministic reading-order logic, and persist OCR results under `ocr/`.

**Step 4: Run test to verify it passes**

Run: `python -m pytest apps/cli/tests/test_reading_order.py apps/cli/tests/test_ocr_command.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add apps/cli
git commit -m "feat: add manga ocr pipeline"
```

### Task 7: Build Review and Classification Stage

**Files:**
- Create: `apps/cli/app/commands/review.py`
- Create: `apps/cli/app/services/review_state.py`
- Create: `apps/cli/tests/test_review_command.py`
- Modify: `apps/api/app/models/frame.py`

**Step 1: Write the failing test**

Write tests that verify:
- reviewed text can override OCR text
- order can be changed
- bubble kind can be changed to `dialogue`, `narration`, `sfx`, or `ignore`
- skipped review pages remain editable later

**Step 2: Run test to verify it fails**

Run: `python -m pytest apps/cli/tests/test_review_command.py -v`
Expected: FAIL because review persistence is not implemented.

**Step 3: Write minimal implementation**

Add review persistence and a CLI review command that updates reviewed bubble data instead of mutating raw OCR output.

**Step 4: Run test to verify it passes**

Run: `python -m pytest apps/cli/tests/test_review_command.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add apps/cli apps/api
git commit -m "feat: add reviewed text workflow"
```

### Task 8: Add Translation and Script Normalization

**Files:**
- Create: `apps/cli/app/commands/translate.py`
- Create: `apps/cli/app/services/translation_service.py`
- Create: `apps/cli/app/services/script_builder.py`
- Create: `apps/cli/tests/test_script_builder.py`

**Step 1: Write the failing test**

Write tests that verify:
- translation output is stored separately from OCR and reviewed text
- spoken script text can differ from translated source text
- subtitle text can be shorter than spoken script text

**Step 2: Run test to verify it fails**

Run: `python -m pytest apps/cli/tests/test_script_builder.py -v`
Expected: FAIL because translation and script builder logic does not exist.

**Step 3: Write minimal implementation**

Implement a translation stage interface and a script builder that stores source text, translated text, voice text, and subtitle text separately.

**Step 4: Run test to verify it passes**

Run: `python -m pytest apps/cli/tests/test_script_builder.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add apps/cli
git commit -m "feat: add translation and script normalization"
```

### Task 9: Add TTS Integration Layer

**Files:**
- Create: `apps/api/app/integrations/moyin_tts.py`
- Create: `apps/cli/app/commands/voice.py`
- Create: `apps/cli/app/services/voice_generation.py`
- Create: `apps/cli/tests/test_voice_generation.py`
- Create: `apps/api/tests/test_moyin_tts.py`

**Step 1: Write the failing test**

Write tests that verify:
- narrator and character segments map to different voice presets
- generated audio file paths are persisted
- provider errors are surfaced clearly

**Step 2: Run test to verify it fails**

Run: `python -m pytest apps/cli/tests/test_voice_generation.py apps/api/tests/test_moyin_tts.py -v`
Expected: FAIL because the TTS integration does not exist.

**Step 3: Write minimal implementation**

Implement a provider wrapper for Moyin TTS, a CLI voice command, and logic that creates audio files and updates `voices.json`.

**Step 4: Run test to verify it passes**

Run: `python -m pytest apps/cli/tests/test_voice_generation.py apps/api/tests/test_moyin_tts.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add apps/api apps/cli
git commit -m "feat: add tts voice generation"
```

### Task 10: Add Local Recording Workflow

**Files:**
- Create: `apps/cli/app/services/recording.py`
- Create: `apps/cli/app/services/transcription.py`
- Create: `apps/cli/tests/test_recording_flow.py`

**Step 1: Write the failing test**

Write tests that verify:
- recording mode creates an audio artifact
- accepted recordings are linked to the correct voice segment
- re-record replaces prior output cleanly
- skipped recordings do not block later editing

**Step 2: Run test to verify it fails**

Run: `python -m pytest apps/cli/tests/test_recording_flow.py -v`
Expected: FAIL because the recording workflow does not exist.

**Step 3: Write minimal implementation**

Implement a stable MVP recording flow with toggled start/stop capture, artifact persistence, and optional transcription verification.

**Step 4: Run test to verify it passes**

Run: `python -m pytest apps/cli/tests/test_recording_flow.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add apps/cli
git commit -m "feat: add local recording workflow"
```

### Task 11: Build Scene Timeline Generator

**Files:**
- Create: `apps/cli/app/commands/build_scenes.py`
- Create: `apps/cli/app/services/scene_builder.py`
- Create: `apps/cli/tests/test_scene_builder.py`

**Step 1: Write the failing test**

Write tests that verify:
- audio-backed scenes use audio duration plus configurable padding
- textless frames create `silent` scenes with default durations
- scene files are written in render-ready order

**Step 2: Run test to verify it fails**

Run: `python -m pytest apps/cli/tests/test_scene_builder.py -v`
Expected: FAIL because the scene builder does not exist.

**Step 3: Write minimal implementation**

Implement a scene generator that reads reviewed frames and voice data, then writes `script/scenes.json`.

**Step 4: Run test to verify it passes**

Run: `python -m pytest apps/cli/tests/test_scene_builder.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add apps/cli
git commit -m "feat: add scene timeline generation"
```

### Task 12: Create Remotion MVP Composition

**Files:**
- Create: `apps/remotion/src/Root.tsx`
- Create: `apps/remotion/src/VideoComposition.tsx`
- Create: `apps/remotion/src/components/scenes/NarrationScene.tsx`
- Create: `apps/remotion/src/components/scenes/DialogueScene.tsx`
- Create: `apps/remotion/src/components/scenes/SilentScene.tsx`
- Create: `apps/remotion/src/components/common/Subtitles.tsx`
- Create: `apps/remotion/src/components/common/ImageMotion.tsx`
- Create: `apps/remotion/src/tests/video-composition.test.tsx`

**Step 1: Write the failing test**

Write tests that verify:
- the composition renders all scene types
- scene durations match `scenes.json`
- subtitles render for narration and dialogue scenes

**Step 2: Run test to verify it fails**

Run: `npm test --workspace apps/remotion`
Expected: FAIL because the Remotion project is not implemented.

**Step 3: Write minimal implementation**

Implement the Root composition, a scene switcher, and three stable scene templates with basic image motion and subtitles.

**Step 4: Run test to verify it passes**

Run: `npm test --workspace apps/remotion`
Expected: PASS

**Step 5: Commit**

```bash
git add apps/remotion
git commit -m "feat: add remotion scene renderer"
```

### Task 13: Add FastAPI Project Read APIs

**Files:**
- Create: `apps/api/app/main.py`
- Create: `apps/api/app/routes/projects.py`
- Create: `apps/api/app/routes/scenes.py`
- Create: `apps/api/tests/test_projects_api.py`

**Step 1: Write the failing test**

Write API tests that verify:
- project lists can be read
- project details include progress and file-backed status
- scenes can be fetched for preview

**Step 2: Run test to verify it fails**

Run: `python -m pytest apps/api/tests/test_projects_api.py -v`
Expected: FAIL because the API routes do not exist.

**Step 3: Write minimal implementation**

Implement FastAPI app setup and read-only project and scene routes backed by the file-store layer.

**Step 4: Run test to verify it passes**

Run: `python -m pytest apps/api/tests/test_projects_api.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add apps/api
git commit -m "feat: add project read api"
```

### Task 14: Add Web Project Overview and Preview

**Files:**
- Create: `apps/web/src/App.tsx`
- Create: `apps/web/src/pages/ProjectOverview.tsx`
- Create: `apps/web/src/pages/PreviewPage.tsx`
- Create: `apps/web/src/lib/api.ts`
- Create: `apps/web/src/tests/project-overview.test.tsx`

**Step 1: Write the failing test**

Write tests that verify:
- project overview renders project status sections
- preview page can load scene data
- remotion preview container mounts without crashing

**Step 2: Run test to verify it fails**

Run: `npm test --workspace apps/web`
Expected: FAIL because the web app is not implemented.

**Step 3: Write minimal implementation**

Implement a small React app with a project overview page and a preview page that fetches API data and embeds the Remotion player.

**Step 4: Run test to verify it passes**

Run: `npm test --workspace apps/web`
Expected: PASS

**Step 5: Commit**

```bash
git add apps/web
git commit -m "feat: add project overview and preview ui"
```

### Task 15: Add Web OCR Review Page

**Files:**
- Create: `apps/web/src/pages/FrameReviewPage.tsx`
- Create: `apps/api/app/routes/review.py`
- Create: `apps/api/tests/test_review_api.py`
- Create: `apps/web/src/tests/frame-review.test.tsx`

**Step 1: Write the failing test**

Write tests that verify:
- frame review data can be loaded
- reviewed text can be updated
- bubble order and kind can be edited and persisted

**Step 2: Run test to verify it fails**

Run: `python -m pytest apps/api/tests/test_review_api.py -v`
Expected: FAIL because review APIs are missing.

Run: `npm test --workspace apps/web`
Expected: FAIL because the frame review page does not exist.

**Step 3: Write minimal implementation**

Implement review write APIs and a web page that edits reviewed bubble content, order, speaker, and kind.

**Step 4: Run test to verify it passes**

Run: `python -m pytest apps/api/tests/test_review_api.py -v`
Expected: PASS

Run: `npm test --workspace apps/web`
Expected: PASS

**Step 5: Commit**

```bash
git add apps/api apps/web
git commit -m "feat: add ocr review interface"
```

### Task 16: Add Web Scene and Audio Review

**Files:**
- Create: `apps/web/src/pages/SceneReviewPage.tsx`
- Create: `apps/api/app/routes/voice.py`
- Create: `apps/api/tests/test_voice_api.py`
- Create: `apps/web/src/tests/scene-review.test.tsx`

**Step 1: Write the failing test**

Write tests that verify:
- scenes and associated audio metadata are listed
- subtitle text can be edited
- duration and style preset can be edited
- audio replacement actions are exposed

**Step 2: Run test to verify it fails**

Run: `python -m pytest apps/api/tests/test_voice_api.py -v`
Expected: FAIL because voice APIs do not exist.

Run: `npm test --workspace apps/web`
Expected: FAIL because the scene review page does not exist.

**Step 3: Write minimal implementation**

Implement scene and voice metadata APIs and a web page that supports light scene and audio review.

**Step 4: Run test to verify it passes**

Run: `python -m pytest apps/api/tests/test_voice_api.py -v`
Expected: PASS

Run: `npm test --workspace apps/web`
Expected: PASS

**Step 5: Commit**

```bash
git add apps/api apps/web
git commit -m "feat: add scene and audio review"
```

### Task 17: Add Render Trigger and Job Status

**Files:**
- Create: `apps/api/app/routes/render.py`
- Create: `apps/api/app/services/render_jobs.py`
- Create: `apps/api/tests/test_render_api.py`
- Modify: `apps/web/src/pages/PreviewPage.tsx`

**Step 1: Write the failing test**

Write tests that verify:
- render jobs can be triggered
- job status can be polled
- preview page shows render progress

**Step 2: Run test to verify it fails**

Run: `python -m pytest apps/api/tests/test_render_api.py -v`
Expected: FAIL because render job logic does not exist.

**Step 3: Write minimal implementation**

Implement a simple file-backed render job service and wire it into the preview page so the user can trigger preview and final renders.

**Step 4: Run test to verify it passes**

Run: `python -m pytest apps/api/tests/test_render_api.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add apps/api apps/web
git commit -m "feat: add render jobs and status"
```

### Task 18: Wire the Guided `run` Command

**Files:**
- Create: `apps/cli/app/commands/run.py`
- Create: `apps/cli/tests/test_run_command.py`
- Modify: `apps/cli/app/main.py`

**Step 1: Write the failing test**

Write tests that verify:
- `run` walks the user through unfinished stages
- completed stages are skipped automatically
- project progress is shown from file-backed state

**Step 2: Run test to verify it fails**

Run: `python -m pytest apps/cli/tests/test_run_command.py -v`
Expected: FAIL because the guided command is not implemented.

**Step 3: Write minimal implementation**

Implement the guided CLI command that reads project status and routes the user through import, OCR, review, translation, voice, scene build, and preview stages.

**Step 4: Run test to verify it passes**

Run: `python -m pytest apps/cli/tests/test_run_command.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add apps/cli
git commit -m "feat: add guided workflow command"
```

### Task 19: Add Documentation and Local Setup Guide

**Files:**
- Modify: `README.md`
- Create: `docs/setup/local-development.md`
- Create: `docs/setup/moyin-env.md`
- Create: `docs/setup/mangaocr.md`

**Step 1: Write the failing test**

Write a docs checklist test or manual verification checklist that requires:
- local setup instructions for Python and Node
- MangaOCR dependency instructions
- Moyin environment configuration
- commands for starting CLI, API, web, and Remotion

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/docs/test_setup_docs.py -v`
Expected: FAIL because the setup documentation does not exist.

**Step 3: Write minimal implementation**

Add concise setup docs and top-level README sections that explain local development and expected environment variables.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/docs/test_setup_docs.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add README.md docs tests/docs/test_setup_docs.py
git commit -m "docs: add local setup guidance"
```

### Task 20: Verify the End-to-End MVP

**Files:**
- Create: `docs/verification/mvp-checklist.md`
- Create: `tests/e2e/test_mvp_flow.md`

**Step 1: Write the failing test**

Define an end-to-end verification checklist that covers:
- creating a project
- importing images
- running OCR
- reviewing text
- creating voice assets
- building scenes
- previewing in web
- triggering a render

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/e2e -v`
Expected: FAIL or SKIP until the workflow exists end to end.

**Step 3: Write minimal implementation**

Add the verification checklist and any missing glue code required to execute the MVP manually from start to finish.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/e2e -v`
Expected: PASS or documented SKIP with clear prerequisites

**Step 5: Commit**

```bash
git add docs/verification tests/e2e
git commit -m "test: add mvp verification checklist"
```

## Notes

- This directory is currently not a git repository, so the commit steps above cannot be executed until the project is initialized as a repository.
- The brainstorming workflow usually expects a dedicated worktree, which is also blocked until git is initialized.
- Prefer implementing the plan in small slices and verifying each task before moving to the next one.
