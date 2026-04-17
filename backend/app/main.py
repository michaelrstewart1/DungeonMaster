import logging
import os
from contextlib import asynccontextmanager

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:     %(name)s - %(message)s",
)

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

    Supports Gemini, OpenAI, Anthropic, and Ollama LLM providers based on config.
    Falls back to None / FakeTTS so unit-tests still pass without network calls.
    """
    from app.config import settings
    from app.services.llm.narrator import DMNarrator
    from app.services.llm.openai import OpenAIProvider
    from app.services.llm.ollama import OllamaProvider
    from app.services.llm.gemini import GeminiProvider
    from app.services.llm.anthropic import AnthropicProvider
    from app.services.voice.tts import FakeTTS, OpenAITTS

    narrator = None
    tts = FakeTTS()

    provider = settings.llm_provider.lower()

    if provider == "gemini" and settings.gemini_api_key:
        try:
            llm = GeminiProvider(
                api_key=settings.gemini_api_key,
                model=settings.gemini_model,
            )
            narrator = DMNarrator(llm=llm, max_history=30)
            logger.info(
                "AI DM: Gemini narrator ready (model=%s)",
                settings.gemini_model,
            )
        except Exception as exc:  # pragma: no cover
            logger.warning("AI DM: could not init Gemini (%s) — using fallbacks", exc)

    elif provider == "anthropic" and settings.anthropic_api_key:
        try:
            llm = AnthropicProvider(api_key=settings.anthropic_api_key)
            narrator = DMNarrator(llm=llm, max_history=30)
            logger.info("AI DM: Anthropic narrator ready")
        except Exception as exc:  # pragma: no cover
            logger.warning("AI DM: could not init Anthropic (%s) — using fallbacks", exc)

    elif provider == "ollama":
        try:
            llm = OllamaProvider(
                base_url=settings.ollama_base_url,
                model=settings.ollama_model,
            )
            narrator = DMNarrator(llm=llm, max_history=30)
            logger.info(
                "AI DM: Ollama narrator ready (model=%s, url=%s)",
                settings.ollama_model,
                settings.ollama_base_url,
            )
        except Exception as exc:  # pragma: no cover
            logger.warning("AI DM: could not init Ollama (%s) — using fallbacks", exc)

    elif provider == "openai" and settings.openai_api_key:
        try:
            llm = OpenAIProvider(api_key=settings.openai_api_key)
            narrator = DMNarrator(llm=llm, max_history=30)
            logger.info("AI DM: OpenAI narrator ready (model=gpt-4.1-mini)")
        except Exception as exc:  # pragma: no cover
            logger.warning("AI DM: could not init OpenAI services (%s) — using fallbacks", exc)

    if narrator is None:
        logger.warning("AI DM: No LLM provider active (provider=%s) — using keyword fallbacks", provider)

    # TTS is independent of the narrator LLM — use OpenAI TTS whenever key is available
    if settings.openai_api_key:
        try:
            tts = OpenAITTS(
                api_key=settings.openai_api_key,
                voice=settings.openai_tts_voice,
                model=settings.openai_tts_model,
            )
            logger.info("TTS: OpenAI TTS ready (voice=%s)", settings.openai_tts_voice)
        except Exception as exc:  # pragma: no cover
            logger.warning("TTS: could not init OpenAI TTS (%s) — using FakeTTS", exc)

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
    """ASGI lifespan: init DB, boot narrator/TTS on startup, clean up on shutdown."""
    from app.db import async_session, init_db

    # Create all ORM tables
    await init_db()

    # Expose session factory for WebSocket handler
    app.state.db_factory = async_session

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
