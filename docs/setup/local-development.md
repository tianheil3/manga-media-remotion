# Local Development

## Prerequisites

- Python 3.12 or newer
- Node.js 20 or newer
- `npm`
- `ffmpeg`

## Install Python Dependencies

Create or activate your Python environment, then install the runtime and test dependencies used by `apps/cli` and `apps/api`.

Example:

```bash
python -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn typer pytest
```

Install any additional OCR or audio dependencies from the dedicated setup guides before running pipeline stages that need them.

After installing the CLI dependencies and provider configuration, run the setup check:

```bash
python -m apps.cli.app.main doctor
```

`doctor` verifies media tooling (`python`, `node`, `ffmpeg`) plus the active OCR, translation, and TTS prerequisites.

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

Run the shared schema tests:

```bash
npm test --workspace packages/schema
```

## App Entry Points

- `apps/cli`: `python -m apps.cli.app.main --help`
- `apps/api`: `uvicorn apps.api.app.main:app --reload`
- `apps/web`: reserved for the React review UI
- `apps/remotion`: reserved for the Remotion renderer
