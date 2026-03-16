# Operator Runbook

Use this runbook when you need to take a project from a new workspace to a verified final render in the current MVP.

The workflow stays local-first. Every stage reads or writes `workspace/<project-id>/`, so operators can stop after any command, inspect the generated files, and resume the same project later.

## Preflight

1. Install the local dependencies from [local-development.md](./local-development.md).
2. Confirm provider setup with:

```bash
python -m apps.cli.app.main doctor
```

3. If you need a known-good regression path without OCR or live providers, run:

```bash
bash scripts/smoke-sample-project.sh
```

## Workspace Layout

The operator-facing artifacts live under `workspace/<project-id>/`:

- `project.json` and `config.json`: project metadata
- `images/`: imported source pages
- `ocr/`: per-frame OCR output
- `script/frames.json`: imported frame list plus OCR and review data
- `script/script.json`: translated, voice, and subtitle text layers
- `script/voices.json`: generated voice metadata
- `script/scenes.json`: render-ready scene timeline
- `renders/`: preview and final outputs plus `jobs.json`

## Happy Path

### 1. Create the project

```bash
python -m apps.cli.app.main new <project-id> --title "Operator Run" --workspace-root workspace
```

Expected result: `workspace/<project-id>/` exists with `project.json`, `config.json`, and empty `script/*.json` files.

### 2. Import images in operator order

```bash
python -m apps.cli.app.main import-images <project-id> /path/to/page-001.png /path/to/page-002.png --workspace-root workspace
```

Expected result: imported files land in `workspace/<project-id>/images/`, and `script/frames.json` contains one frame entry per image.

### 3. Run OCR

```bash
MANGA_IMAGE_TRANSLATOR_BASE_URL=... \
python -m apps.cli.app.main ocr <project-id> --workspace-root workspace
```

Expected result: `ocr/*.json` files are created and each frame in `script/frames.json` gains `bubbles`.

### 4. Review OCR text

Use the CLI for file-driven review updates:

```bash
python -m apps.cli.app.main review <project-id> frame-001 --review-file /tmp/review.json --workspace-root workspace
```

Or skip a frame without editing it yet:

```bash
python -m apps.cli.app.main review <project-id> frame-001 --skip --workspace-root workspace
```

Expected result: reviewed text stays separate from OCR text in `script/frames.json` under `reviewedBubbles`.

### 5. Translate and preserve downstream text layers

```bash
MANGA_IMAGE_TRANSLATOR_BASE_URL=... \
python -m apps.cli.app.main translate <project-id> --target-language zh --workspace-root workspace
```

Expected result: `script/script.json` is written with separate `sourceText`, `translatedText`, `voiceText`, and `subtitleText` values.

### 6. Generate voice assets

```bash
MOYIN_TTS_BASE_URL=... \
MOYIN_TTS_API_KEY=... \
python -m apps.cli.app.main voice <project-id> --workspace-root workspace
```

Expected result: `script/voices.json` is populated and audio files land under `audio/`.

### 7. Build scenes and confirm project progress

```bash
python -m apps.cli.app.main build-scenes <project-id> --workspace-root workspace
python -m apps.cli.app.main run <project-id> --workspace-root workspace
python -m apps.cli.app.main integrity <project-id> --workspace-root workspace
```

Expected result:

- `script/scenes.json` exists
- `run` reports `Next stage: complete`
- `integrity` prints `Project integrity OK.`

### 8. Start the review stack

```bash
MANGA_WORKSPACE_ROOT="$(pwd)/workspace" uvicorn apps.api.app.main:app --host 127.0.0.1 --port 8000
MANGA_API_BASE_URL=http://127.0.0.1:8000 npm run dev --workspace apps/web -- --host 127.0.0.1 --port 4173
```

Useful checks:

```bash
curl -s http://127.0.0.1:8000/projects/<project-id> | python -m json.tool
curl -s http://127.0.0.1:8000/projects/<project-id>/frames | python -m json.tool
curl -s http://127.0.0.1:8000/projects/<project-id>/scene-review | python -m json.tool
curl -s http://127.0.0.1:4173/?projectId=<project-id>
```

### 9. Trigger preview and final renders

Preview render:

```bash
curl -s -X POST -H 'content-type: application/json' \
  -d '{"kind":"preview"}' \
  http://127.0.0.1:8000/projects/<project-id>/render-jobs | python -m json.tool
```

Final render:

```bash
curl -s -X POST -H 'content-type: application/json' \
  -d '{"kind":"final"}' \
  http://127.0.0.1:8000/projects/<project-id>/render-jobs | python -m json.tool
```

Poll `/render-jobs/<job-id>` until the job reaches `completed`, then verify the output file exists under `workspace/<project-id>/renders/`.

## Failure Triage

### OCR triage

- If `doctor` or `ocr` says `Manga Image Translator OCR is not configured`, export `MANGA_IMAGE_TRANSLATOR_BASE_URL`; set `MANGA_IMAGE_TRANSLATOR_OCR_PATH` or `MANGA_IMAGE_TRANSLATOR_API_KEY` when your MIT service uses a non-default endpoint or bearer auth.
- If `ocr` says `No imported frames found. Run import-images first.`, re-run `import-images` and confirm `script/frames.json` is not empty.
- After a partial OCR run, inspect both `workspace/<project-id>/ocr/` and `workspace/<project-id>/script/frames.json` before retrying.

### Translation triage

- If translation fails with `Manga Image Translator translation is not configured`, export `MANGA_IMAGE_TRANSLATOR_BASE_URL`; set `MANGA_IMAGE_TRANSLATOR_TRANSLATE_PATH` or `MANGA_IMAGE_TRANSLATOR_API_KEY` when your MIT service uses a non-default endpoint or bearer auth.
- If translation fails with `No reviewed text found. Run review before translation.`, confirm reviewed entries were saved to `reviewedBubbles`.
- If translation fails for a specific bubble, the error includes the bubble and frame IDs. Fix the provider or input and rerun `translate`.
- Confirm `script/script.json` is updated only after a successful run. Do not hand-edit it unless you are intentionally applying operator overrides.

### TTS triage

- If `voice` fails with `Moyin TTS is not configured`, export `MOYIN_TTS_BASE_URL` and `MOYIN_TTS_API_KEY`.
- If `voice` fails with `No script entries found. Run translate before voice generation.`, verify `script/script.json` exists and contains entries.
- If a request fails for one script entry, the error includes the script ID. Fix the provider and rerun `voice`.
- Confirm generated WAV files exist under `audio/` and that `script/voices.json` points at the same relative paths.

### Media generation triage

- If `build-scenes` fails with `No voice segments found. Run voice before building scenes.`, restore `script/voices.json` or rerun `voice`.
- If `build-scenes` fails with `No frames found. Import images before building scenes.`, verify `images/` and `script/frames.json`.
- Run `python -m apps.cli.app.main integrity <project-id> --workspace-root workspace` to surface missing project files, missing media files, or broken scene/voice references.
- Run `python -m apps.cli.app.main repair <project-id> --workspace-root workspace` to recreate missing JSON files and resync repairable scene/voice links.

### Render job triage

- If render jobs fail immediately, check `workspace/<project-id>/renders/jobs.json` for the persisted `errorMessage`.
- `Missing project.json for render job.` usually means the API was started with a relative `MANGA_WORKSPACE_ROOT`. Restart it with an absolute path such as `MANGA_WORKSPACE_ROOT="$(pwd)/workspace"`.
- `Missing script/scenes.json for render job.` means the project has not completed `build-scenes`, or the file was removed after scene generation.
- If the renderer exits non-zero, rerun `integrity`, verify `script/scenes.json`, and confirm the referenced media files still exist before retrying the render.

## Operator Handoff

Before handoff, complete the release checks in [mvp-checklist.md](../verification/mvp-checklist.md) and attach the exact command log, generated artifact paths, and any recovery steps that were needed during the run.
