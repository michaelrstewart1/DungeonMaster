import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

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

logger = logging.getLogger(__name__)


def _init_app_state(app: FastAPI) -> None:
    """Initialize narrator and TTS on app startup.

    When an OpenAI API key is configured the app uses real GPT-4o narration
    and the onyx TTS voice (deep, wizard-like).  When no key is present we fall
    back to None / FakeTTS so all unit-tests still pass without network calls.
    """
    from app.config import settings
    from app.services.llm.narrator import DMNarrator
    from app.services.llm.openai import OpenAIProvider
    from app.services.voice.tts import FakeTTS, OpenAITTS

    narrator = None
    tts = FakeTTS()

    if settings.openai_api_key:
        try:
            llm = OpenAIProvider(api_key=settings.openai_api_key)
            narrator = DMNarrator(llm=llm, max_history=30)
            tts = OpenAITTS(
                api_key=settings.openai_api_key,
                voice=settings.openai_tts_voice,
                model=settings.openai_tts_model,
            )
            logger.info("AI DM: GPT-4o narrator + OpenAI TTS (voice=%s) ready", settings.openai_tts_voice)
        except Exception as exc:  # pragma: no cover
            logger.warning("AI DM: could not init OpenAI services (%s) — using fallbacks", exc)

    app.state.narrator = narrator
    app.state.tts = tts

    # Vision: wire GPT-4o analyzer when OpenAI key is available
    vision_analyzer = None
    if settings.openai_api_key:
        try:
            from app.services.vision.gpt4_analyzer import GPT4VisionAnalyzer
            vision_analyzer = GPT4VisionAnalyzer(api_key=settings.openai_api_key)
            logger.info("Vision: GPT-4o board analyzer ready")
        except Exception as exc:  # pragma: no cover
            logger.warning("Vision: could not init GPT-4o analyzer (%s) — using fake", exc)
    app.state.vision_analyzer = vision_analyzer


@asynccontextmanager
async def lifespan(app: FastAPI):
    """ASGI lifespan: boot narrator/TTS on startup, clean up on shutdown."""
    _init_app_state(app)
    yield
    # Shutdown — close any open HTTP clients
    narrator = getattr(app.state, "narrator", None)
    if narrator is not None:
        llm = getattr(narrator, "_llm", None)
        client = getattr(llm, "_client", None)
        if client is not None:
            try:
                await client.aclose()
            except Exception:
                pass
    tts = getattr(app.state, "tts", None)
    if tts is not None:
        client = getattr(tts, "_client", None)
        if client is not None:
            try:
                await client.aclose()
            except Exception:
                pass


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="AI Dungeon Master",
        description="AI-powered D&D 5e Dungeon Master",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
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

    portraits_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "generated_portraits")
    os.makedirs(portraits_dir, exist_ok=True)
    app.mount("/api/portraits", StaticFiles(directory=portraits_dir), name="portraits")

    return app


app = create_app()
