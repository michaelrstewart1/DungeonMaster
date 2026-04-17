from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "AI Dungeon Master"
    debug: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://dungeonmaster:dungeonmaster@localhost:5432/dungeonmaster"
    database_echo: bool = False

    # MongoDB (SRD data)
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_database: str = "5e-database"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # LLM Settings
    llm_provider: str = "anthropic"  # anthropic, openai, ollama, gemini
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"

    # Voice Settings
    voice_enabled: bool = False
    stt_model: str = "base.en"
    tts_engine: str = "piper"  # piper, xtts, openai

    # OpenAI TTS (wizard voice)
    openai_tts_voice: str = "onyx"   # onyx = deep, gravelly, perfect for wizard DM
    openai_tts_model: str = "tts-1-hd"  # HD model for best quality

    model_config = {"env_prefix": "DM_", "env_file": ".env"}


settings = Settings()
