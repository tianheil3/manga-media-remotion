# Manga Media Remotion

This repository is a local-first manga video workflow MVP.

- `apps/cli` contains the Python CLI for project creation and pipeline stages.
- `apps/api` contains the FastAPI service and file-backed project services.
- `apps/web` contains the React review interface.
- `apps/remotion` contains the Remotion renderer that consumes normalized scene data.
- `packages/schema` contains shared TypeScript schemas for on-disk contracts.
- `packages/shared` is reserved for cross-app utilities.
- `workspace/<project-id>` stores resumable project state on disk instead of in a database.

## Local Development

Setup guides live under `docs/setup/`:

- `docs/setup/local-development.md`
- `docs/setup/mangaocr.md`
- `docs/setup/moyin-env.md`
- `docs/setup/translation-env.md`
- `docs/setup/symphony.md`
- `docs/setup/strict-validation.md`
- `docs/setup/symphony-land.md`

## Runnable Web Review App

`apps/web` now ships a real local review app instead of test-only entrypoints.

Typical local flow:

```bash
uvicorn apps.api.app.main:app --reload
MANGA_API_BASE_URL=http://127.0.0.1:8000 npm run dev --workspace apps/web -- --host 127.0.0.1 --port 4173
```

Required validation for the web app package:

```bash
npm test --workspace apps/web
npm run build --workspace apps/web
```

The browser app also accepts `apiBaseUrl`, `projectId`, `frameId`, and `activeJobId` query parameters so you can deep-link into a review session.

Run `python -m apps.cli.app.main doctor` after local setup changes to verify media tooling plus OCR, translation, and TTS prerequisites.

## Sample Project Smoke

The repository includes a committed workspace-shaped fixture at `tests/fixtures/workspace/demo-001/`.
It covers a minimal completed happy path with separate OCR, reviewed, translated, voice, and scene data plus a tiny image and WAV asset.

Run this smoke path to exercise the CLI progress view, file-backed API reads/media, and preview render against that fixture:

```bash
bash scripts/smoke-sample-project.sh
```

`scripts/verify-strict.sh` includes this smoke command so it can be rerun during regression checks without depending on ad hoc local workspace state.

## Symphony Auto-Land

Symphony landing is repository-defined:

- `WORKFLOW.md` tells Symphony that `Merging` is a landing-only state.
- `scripts/verify-strict.sh` runs the repository strict validation suite.
- `scripts/land.sh` squash-merges an issue branch into `main` and pushes `main` to `origin/main`.
- `docs/verification/symphony-auto-land.md` describes the safe end-to-end verification checklist.
