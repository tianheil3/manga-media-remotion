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
- `docs/setup/operator-runbook.md`
- `docs/setup/manga-image-translator.md`
- `docs/setup/moyin-env.md`
- `docs/setup/translation-env.md`
- `docs/setup/symphony.md`
- `docs/setup/strict-validation.md`
- `docs/setup/symphony-land.md`

## Runnable Monorepo Quickstart

Install the checked-in Node workspace dependencies from the repository root:

```bash
npm install
```

Create or activate your Python environment, install the runtime packages described in `docs/setup/local-development.md`, then verify the local toolchain and provider setup:

```bash
python -m apps.cli.app.main doctor
```

Startup commands for the runnable packages:

```bash
python -m apps.cli.app.main --help
MANGA_WORKSPACE_ROOT="$(pwd)/workspace" uvicorn apps.api.app.main:app --reload
MANGA_API_BASE_URL=http://127.0.0.1:8000 npm run dev --workspace apps/web -- --host 127.0.0.1 --port 4173
npm run render --workspace apps/remotion -- --help
```

`apps/web` is a real local review app, and `apps/remotion` is the renderer CLI that the API uses for preview and final jobs.

Portable project workspaces can be moved between machines with:

```bash
python -m apps.cli.app.main export-workspace demo-001 /tmp/demo-001.tar.gz --workspace-root workspace
python -m apps.cli.app.main import-workspace /tmp/demo-001.tar.gz --workspace-root workspace
```

Package-level validation:

```bash
npm test --workspace apps/web
npm run build --workspace apps/web
npm test --workspace apps/remotion
```

The browser app also accepts `apiBaseUrl`, `projectId`, `frameId`, and `activeJobId` query parameters so you can deep-link into a review session.

Use `MANGA_WORKSPACE_ROOT` as an absolute path when the API will trigger render jobs, and set `MANGA_API_BASE_URL` or `VITE_API_BASE_URL` for the web app when you are not relying on the query parameter override.

The latest checked-in real workflow run record is `docs/verification/mvp-real-run-2026-03-15.md`.

Operator handoff references:

- `docs/setup/operator-runbook.md`
- `docs/verification/mvp-checklist.md`

## Sample Project Smoke

The repository includes a committed workspace-shaped fixture at `tests/fixtures/workspace/demo-001/`.
It covers a minimal completed happy path with separate OCR, reviewed, translated, voice, and scene data plus a tiny image and WAV asset.

Run this smoke path to exercise the CLI progress view, file-backed API reads/media, and preview render against that fixture:

```bash
bash scripts/smoke-sample-project.sh
```

`scripts/verify-strict.sh` includes this smoke command so it can be rerun during regression checks without depending on ad hoc local workspace state.

That same fixture shape is also used by the portability coverage to verify that an exported archive can be imported and still resume review/render progress checks.

## Symphony Auto-Land

Symphony landing is repository-defined:

- `WORKFLOW.md` tells Symphony that `Merging` is a landing-only state.
- `scripts/verify-strict.sh` runs the repository strict validation suite.
- `scripts/land.sh` squash-merges an issue branch into `main` and pushes `main` to `origin/main`.
- `docs/verification/symphony-auto-land.md` describes the safe end-to-end verification checklist.
