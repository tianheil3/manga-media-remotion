import os
from pathlib import Path

from fastapi import FastAPI

from apps.api.app.routes.projects import router as projects_router
from apps.api.app.routes.render import router as render_router
from apps.api.app.routes.review import router as review_router
from apps.api.app.routes.scenes import router as scenes_router
from apps.api.app.routes.voice import router as voice_router


def create_app(*, workspace_root: Path | None = None) -> FastAPI:
    app = FastAPI(title="Manga Media API")
    resolved_workspace_root = workspace_root or os.environ.get("MANGA_WORKSPACE_ROOT") or "workspace"
    app.state.workspace_root = Path(resolved_workspace_root)
    app.include_router(projects_router)
    app.include_router(render_router)
    app.include_router(review_router)
    app.include_router(scenes_router)
    app.include_router(voice_router)
    return app


app = create_app()
