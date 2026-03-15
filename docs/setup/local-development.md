# Local Development

## Prerequisites

- Python 3.12 or newer
- Node.js 20 or newer
- `npm`
- `ffmpeg`

## Install Python Dependencies

Create or activate your Python environment, then install the shared runtime and test dependencies used by `apps/cli`, `apps/api`, and the local renderer path that `apps/remotion` drives.

```bash
python -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn typer pytest opencv-python numpy Pillow
```

Stage-specific setup:

- OCR: install `manga-ocr` as documented in `docs/setup/mangaocr.md`
- Translation: export the DeepL variables from `docs/setup/translation-env.md`
- TTS: export the Moyin variables from `docs/setup/moyin-env.md`

After installing packages and configuring any provider environment variables, run the shared setup check:

```bash
python -m apps.cli.app.main doctor
```

`doctor` verifies media tooling (`python`, `node`, `ffmpeg`), local render dependencies (`opencv-python`, `numpy`, `Pillow`), plus the active OCR, translation, and TTS prerequisites.

## Install Node Dependencies

Install the checked-in workspace dependencies once from the repository root:

```bash
npm install
```

That root install covers `apps/web`, `apps/remotion`, and `packages/schema`. There is no separate package-install step for the web or Remotion apps.

## Environment Variables

The runnable monorepo uses a small set of environment variables during local startup:

- `MANGA_WORKSPACE_ROOT`: API workspace root. Use an absolute path such as `$(pwd)/workspace` when the API will read or write render jobs for `workspace/<project-id>/`.
- `MANGA_API_BASE_URL`: preferred API base URL for the web dev server and static build.
- `VITE_API_BASE_URL`: alternate web API base URL when you are not using `MANGA_API_BASE_URL`.
- `TRANSLATION_PROVIDER=deepl` and `DEEPL_API_KEY`: required for CLI translation. `DEEPL_BASE_URL` is optional.
- `MOYIN_TTS_BASE_URL` and `MOYIN_TTS_API_KEY`: required for CLI voice generation.
- OCR does not need environment variables, but it does require the `manga-ocr` Python package.

The web app resolves its API URL in this order:

1. `apiBaseUrl` query parameter
2. `MANGA_API_BASE_URL`
3. `VITE_API_BASE_URL`
4. the value typed into the app UI

Example direct link:

```text
http://127.0.0.1:4173/?apiBaseUrl=http%3A%2F%2F127.0.0.1%3A8000&projectId=demo-001
```

## Operator References

Use these docs together when you are running the MVP for handoff instead of just setting up local development:

- `docs/setup/operator-runbook.md`
- `docs/verification/mvp-checklist.md`
- `docs/verification/mvp-real-run-2026-03-15.md`

## Startup Flows

### CLI

Inspect the available commands:

```bash
python -m apps.cli.app.main --help
```

Typical local-first commands still read and write `workspace/<project-id>/` by default, and you can override that with `--workspace-root` when needed:

```bash
python -m apps.cli.app.main new demo-001 --title "Demo Project" --workspace-root workspace
python -m apps.cli.app.main run demo-001 --workspace-root workspace
```

To move a prepared project workspace to another machine or session, export it as a portable archive and import it into another workspace root:

```bash
python -m apps.cli.app.main export-workspace demo-001 /tmp/demo-001.tar.gz --workspace-root workspace
python -m apps.cli.app.main import-workspace /tmp/demo-001.tar.gz --workspace-root workspace
```

The archive preserves the full `workspace/<project-id>/` directory so review data, script data, audio, renders, and any cached project state move together.

### API

Start the FastAPI service from the repository root:

```bash
MANGA_WORKSPACE_ROOT="$(pwd)/workspace" uvicorn apps.api.app.main:app --reload
```

Use an absolute `MANGA_WORKSPACE_ROOT` when you plan to trigger preview or final render jobs through the API. A relative `workspace` root can cause Remotion render jobs to fail to resolve `project.json`.

### Web

Start the review UI in a second terminal after the API is up:

```bash
MANGA_API_BASE_URL=http://127.0.0.1:8000 npm run dev --workspace apps/web -- --host 127.0.0.1 --port 4173
```

Open `http://127.0.0.1:4173/` in a browser and load a project by ID. The running app renders the project overview, frame review, scene review, and preview pages against the live API.

Build the static review app with the same API base URL contract:

```bash
MANGA_API_BASE_URL=http://127.0.0.1:8000 npm run build --workspace apps/web
```

`npm run build --workspace apps/web` writes a static review app to `apps/web/dist/`.

The generated HTML uses an import map that loads `react` and `react-dom/client` from `esm.sh`, so the browser needs outbound internet access when opening the built app.

### Remotion

`apps/remotion` is a runnable renderer package, not a reserved placeholder. Start by printing the CLI contract:

```bash
npm run render --workspace apps/remotion -- --help
```

To render directly from a prepared project workspace, point the CLI at a project that already has `project.json` and `script/scenes.json`:

```bash
npm run render --workspace apps/remotion -- \
  --project-dir "$(pwd)/workspace/<project-id>" \
  --kind preview \
  --output-file renders/manual-preview.mp4
```

Change `--kind` to `final` for final-output runs. The API render-job endpoints call this same package internally, so there is no separate long-running Remotion server to boot.

## Common Commands

Run the CLI tests:

```bash
python -m pytest apps/cli/tests -v
```

Run the API tests:

```bash
python -m pytest apps/api/tests -v
```

Run the reproducible sample-project smoke path:

```bash
bash scripts/smoke-sample-project.sh
```

The smoke fixture lives at `tests/fixtures/workspace/demo-001/`. It is a committed single-project workspace snapshot with one image, one OCR bubble, one reviewed bubble, one translated script entry, one voice asset, and one rendered-scene input so the MVP happy path can be rechecked without OCR or TTS setup.

Run the shared schema tests:

```bash
npm test --workspace packages/schema
```

Run the web review app tests:

```bash
npm test --workspace apps/web
```

Run the Remotion renderer tests:

```bash
npm test --workspace apps/remotion
```
