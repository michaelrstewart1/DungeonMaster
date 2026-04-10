from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.campaigns import router as campaigns_router
from app.api.routes.characters import router as characters_router
from app.api.routes.game import router as game_router
from app.api.routes.maps import router as maps_router
from app.api.routes.auth import router as auth_router
from app.api.routes.vision import router as vision_router
from app.api.routes.avatar import router as avatar_router
from app.api.routes.srd import router as srd_router
from app.api.websockets.game_ws import router as game_ws_router
from app.api.websockets.audio_ws import router as audio_ws_router


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
    app.include_router(maps_router, prefix="/api", tags=["maps"])
    app.include_router(auth_router, prefix="/api", tags=["auth"])
    app.include_router(vision_router, prefix="/api", tags=["vision"])
    app.include_router(avatar_router, prefix="/api", tags=["avatar"])
    app.include_router(srd_router, prefix="/api", tags=["srd"])
    app.include_router(game_ws_router, tags=["websocket"])
    app.include_router(audio_ws_router, tags=["websocket"])

    return app


app = create_app()
