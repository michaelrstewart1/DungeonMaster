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
from app.api.routes.trade import router as trade_router
from app.api.routes.items import router as items_router
from app.api.websockets.game_ws import router as game_ws_router
from app.api.websockets.audio_ws import router as audio_ws_router

logger = logging.getLogger(__name__)


def _build_llm_provider(name: str, settings):
    """Construct an LLM provider by name, or None if unavailable/misconfigured."""
    from app.services.llm.openai import OpenAIProvider
    from app.services.llm.ollama import OllamaProvider
    from app.services.llm.gemini import GeminiProvider
    from app.services.llm.anthropic import AnthropicProvider

    try:
        if name == "gemini" and settings.gemini_api_key:
            return GeminiProvider(api_key=settings.gemini_api_key, model=settings.gemini_model)
        if name == "anthropic" and settings.anthropic_api_key:
            return AnthropicProvider(api_key=settings.anthropic_api_key)
        if name == "ollama":
            return OllamaProvider(base_url=settings.ollama_base_url, model=settings.ollama_model)
        if name == "openai" and settings.openai_api_key:
            return OpenAIProvider(api_key=settings.openai_api_key)
    except Exception as exc:  # pragma: no cover
        logger.warning("AI DM: could not init %s provider (%s)", name, exc)
    return None


def _init_app_state(app: FastAPI) -> None:
    """Initialize narrator and TTS on app startup.

    Supports Gemini, OpenAI, Anthropic, and Ollama LLM providers based on config.
    An optional fallback provider (DM_LLM_FALLBACK_PROVIDER) is chained so a
    dead API never stalls the table. Falls back to None / FakeTTS so
    unit-tests still pass without network calls.
    """
    from app.config import settings
    from app.services.llm.narrator import DMNarrator
    from app.services.llm.fallback import FallbackLLMProvider
    from app.services.voice.tts import FakeTTS, OpenAITTS

    narrator = None
    tts = FakeTTS()

    provider = settings.llm_provider.lower()
    llm = _build_llm_provider(provider, settings)

    fallback_name = (settings.llm_fallback_provider or "").lower()
    if llm is not None and fallback_name and fallback_name != provider:
        fallback = _build_llm_provider(fallback_name, settings)
        if fallback is not None:
            llm = FallbackLLMProvider(llm, fallback)
            logger.info("AI DM: fallback provider chained (%s → %s)", provider, fallback_name)

    if llm is not None:
        narrator = DMNarrator(llm=llm, max_history=30)
        logger.info("AI DM: narrator ready (provider=%s)", llm.name)

    if narrator is None:
        logger.warning("AI DM: No LLM provider active (provider=%s) — using keyword fallbacks", provider)

    # TTS is independent of the narrator LLM — use OpenAI TTS whenever key is available
    if settings.openai_api_key:
        try:
            tts = OpenAITTS(
                api_key=settings.openai_api_key,
                voice=settings.openai_tts_voice,
                model=settings.openai_tts_model,
                speed=settings.openai_tts_speed,
            )
            logger.info("TTS: OpenAI TTS ready (model=%s, voice=%s, speed=%.1f)",
                         settings.openai_tts_model, settings.openai_tts_voice, settings.openai_tts_speed)
        except Exception as exc:  # pragma: no cover
            logger.warning("TTS: could not init OpenAI TTS (%s) — using FakeTTS", exc)

    app.state.narrator = narrator
    app.state.tts = tts

    # STT: real speech-to-text for push-to-talk (phones send webm/opus)
    from app.services.voice.pipeline import VoicePipeline
    from app.services.voice.stt import FakeSTT, OpenAIWhisperSTT, WhisperSTT
    from app.services.voice.vad import VADProcessor

    stt = None
    stt_pref = (settings.stt_provider or "auto").lower()
    if stt_pref in ("auto", "openai") and settings.openai_api_key:
        try:
            stt = OpenAIWhisperSTT(api_key=settings.openai_api_key)
            logger.info("STT: OpenAI Whisper API ready")
        except Exception as exc:  # pragma: no cover
            logger.warning("STT: could not init OpenAI Whisper (%s)", exc)
    if stt is None and stt_pref in ("auto", "whisper"):
        import importlib.util
        if importlib.util.find_spec("faster_whisper") is not None:
            stt = WhisperSTT(
                model_size=settings.stt_model,
                device=settings.stt_device,
            )
            logger.info("STT: local faster-whisper ready (model=%s, device=%s)",
                        settings.stt_model, settings.stt_device)
        elif stt_pref == "whisper":
            logger.warning("STT: faster-whisper requested but not installed — using FakeSTT")
    if stt is None:
        if stt_pref not in ("fake",):
            logger.warning("STT: no real provider available (pref=%s) — using FakeSTT", stt_pref)
        stt = FakeSTT()

    app.state.stt = stt
    app.state.voice_pipeline = VoicePipeline(stt=stt, tts=tts, vad=VADProcessor())

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

    # Board camera: real device capture when configured (DM_VISION_CAMERA_DEVICE >= 0)
    camera = None
    if settings.vision_camera_device >= 0:
        try:
            from app.services.vision.capture import OpenCVCamera
            camera = OpenCVCamera(device_index=settings.vision_camera_device)
            logger.info("Vision: OpenCV camera ready (device=%d)", settings.vision_camera_device)
        except Exception as exc:  # pragma: no cover
            logger.warning("Vision: could not init camera (%s) — using fake", exc)
    app.state.camera = camera


@asynccontextmanager
async def lifespan(app: FastAPI):
    """ASGI lifespan: init DB, boot narrator/TTS on startup, clean up on shutdown."""
    from app.db import async_session, init_db

    # Create all ORM tables
    await init_db()

    # Expose session factory for WebSocket handler
    app.state.db_factory = async_session

    # Restore persisted runtime state (room codes, players, trades, tokens)
    from app.api import storage
    storage.configure(async_session)
    await storage.load_from_db()

    _init_app_state(app)
    yield

    # Shutdown — snapshot runtime state so restarts don't drop live sessions
    try:
        await storage.persist()
    except Exception:
        pass

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

    @app.middleware("http")
    async def timing_middleware(request, call_next):
        """Per-request timing: X-Process-Time header + structured log line.

        Playtest instrumentation correlates this header with client-side
        timings to split network latency from server processing time.
        """
        import time

        start = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start
        response.headers["X-Process-Time"] = f"{elapsed:.4f}"
        if request.url.path.startswith("/api/") and request.url.path != "/api/health":
            logger.info(
                "REQTIME %s %s %d %.1fms",
                request.method, request.url.path, response.status_code, elapsed * 1000,
            )
        return response

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
    app.include_router(trade_router, prefix="/api", tags=["trade"])
    app.include_router(items_router, prefix="/api", tags=["items"])
    app.include_router(game_ws_router, tags=["websocket"])
    app.include_router(audio_ws_router, tags=["websocket"])

    # Serve generated art from the SAME directories the routes write to —
    # these constants are the single source of truth. (A previous version
    # recomputed the paths here and resolved one directory level higher,
    # so every generated portrait/scene URL 404'd.)
    from app.api.routes.characters import PORTRAITS_DIR
    from app.api.routes.game import SCENE_IMAGES_DIR

    os.makedirs(PORTRAITS_DIR, exist_ok=True)
    app.mount("/api/portraits", StaticFiles(directory=PORTRAITS_DIR), name="portraits")

    os.makedirs(SCENE_IMAGES_DIR, exist_ok=True)
    app.mount("/api/scene-images", StaticFiles(directory=SCENE_IMAGES_DIR), name="scene-images")

    return app


app = create_app()
