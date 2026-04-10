from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.campaigns import router as campaigns_router
from app.api.routes.characters import router as characters_router
from app.api.routes.game import router as game_router


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="AI Dungeon Master",
        description="AI-powered D&D 5e Dungeon Master",
        version="0.1.0",
    )

    app.include_router(health_router, prefix="/api", tags=["health"])
    app.include_router(campaigns_router, prefix="/api", tags=["campaigns"])
    app.include_router(characters_router, prefix="/api", tags=["characters"])
    app.include_router(game_router, prefix="/api", tags=["game"])

    return app


app = create_app()
