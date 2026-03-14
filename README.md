# Manga Media Remotion

This repository is a local-first manga video workflow MVP.

- `apps/cli` contains the Python CLI for project creation and pipeline stages.
- `apps/api` contains the FastAPI service and file-backed project services.
- `apps/web` contains the React review interface.
- `apps/remotion` contains the Remotion renderer that consumes normalized scene data.
- `packages/schema` contains shared TypeScript schemas for on-disk contracts.
- `packages/shared` is reserved for cross-app utilities.
- `workspace/<project-id>` stores resumable project state on disk instead of in a database.
