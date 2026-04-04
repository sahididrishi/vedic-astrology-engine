from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # LLM Provider Keys (all optional — router uses whichever are set)
    GEMINI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    TOGETHER_API_KEY: Optional[str] = None
    OPENROUTER_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    LLM_PREFERRED_PROVIDER: Optional[str] = None

    # External API Keys
    ASTROLOGY_API_KEY: Optional[str] = None
    GEOCODING_API_KEY: Optional[str] = None

    # Infrastructure
    REDIS_URL: str = "redis://localhost:6379/0"
    DATABASE_URL: str = "postgresql+asyncpg://vedic:vedic@localhost:5432/vedic"

    # App Config — API_KEY has no default; app fails to start if not set
    API_KEY: str
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]
    EPHE_PATH: str = "./ephe"

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 10
    RATE_LIMIT_WINDOW: int = 60


@lru_cache
def get_settings() -> Settings:
    return Settings()
