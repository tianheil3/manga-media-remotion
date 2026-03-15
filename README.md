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

## Symphony Auto-Land

Symphony landing is repository-defined:

- `WORKFLOW.md` tells Symphony that `Merging` is a landing-only state.
- `scripts/verify-strict.sh` runs the repository strict validation suite.
- `scripts/land.sh` squash-merges an issue branch into `main` and pushes `main` to `origin/main`.
- `docs/verification/symphony-auto-land.md` describes the safe end-to-end verification checklist.
