# Local Development

## Prerequisites

- Python 3.12 or newer
- Node.js 20 or newer
- `npm`
- `ffmpeg`

## Install Python Dependencies

Create or activate your Python environment, then install the runtime and test dependencies used by `apps/cli`, `apps/api`, and the local video renderer used by `apps/remotion`.

Example:

```bash
python -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn typer pytest
```

Install the renderer packages needed for real preview and final MP4 output:

```bash
pip install opencv-python numpy Pillow
```

Install any additional OCR or audio dependencies from the dedicated setup guides before running pipeline stages that need them.

After installing the CLI dependencies and provider configuration, run the setup check:

```bash
python -m apps.cli.app.main doctor
```

`doctor` verifies media tooling (`python`, `node`, `ffmpeg`), local render dependencies (`opencv-python`, `numpy`, `Pillow`), plus the active OCR, translation, and TTS prerequisites.

## Install Node Dependencies

Install the checked-in workspace dependencies from the repository root:

```bash
npm install
```

The current root workspace includes `packages/schema`. Frontend and Remotion app dependencies are tracked separately and may require additional package access when those app layers are enabled.

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

Build the web review app:

```bash
npm run build --workspace apps/web
```

## App Entry Points

- `apps/cli`: `python -m apps.cli.app.main --help`
- `apps/api`: `uvicorn apps.api.app.main:app --reload`
- `apps/web`: runnable review app via `npm run dev --workspace apps/web`
- `apps/remotion`: reserved for the Remotion renderer

## Run the Review App

Start the API from the repository root:

```bash
MANGA_WORKSPACE_ROOT="$(pwd)/workspace" uvicorn apps.api.app.main:app --reload
```

Then start the web app in a second terminal:

```bash
MANGA_API_BASE_URL=http://127.0.0.1:8000 npm run dev --workspace apps/web -- --host 127.0.0.1 --port 4173
```

Open `http://127.0.0.1:4173/` in a browser and load a project by ID. The running app renders the project overview, frame review, scene review, and preview sections through the existing review shell.

Use an absolute `MANGA_WORKSPACE_ROOT` when you plan to trigger render jobs through the API. A relative `workspace` root can cause Remotion render jobs to fail to resolve `project.json`.

### API Base URL Configuration

The web app resolves the API base URL in this order:

1. `apiBaseUrl` query parameter
2. `MANGA_API_BASE_URL` environment variable
3. `VITE_API_BASE_URL` environment variable
4. the value typed into the app UI

Example direct link:

```text
http://127.0.0.1:4173/?apiBaseUrl=http%3A%2F%2F127.0.0.1%3A8000&projectId=demo-001
```

### Build Output

`npm run build --workspace apps/web` writes a static review app to `apps/web/dist/`.

The generated HTML uses an import map that loads `react` and `react-dom/client` from `esm.sh`, so the browser needs outbound internet access when opening the built app.
