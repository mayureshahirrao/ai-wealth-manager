"""
config.py — Centralized application configuration via pydantic-settings.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
        env_ignore_empty=True,
    )

    APP_NAME: str = "AI Wealth Manager"
    APP_ENV: str = "development"
    APP_VERSION: str = "0.7.1"
    DEBUG: bool = True
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    DATABASE_URL: str = "postgresql+asyncpg://wm_user:wm_password@localhost:5433/wealth_manager"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_ECHO: bool = False

    JWT_SECRET_KEY: str = "change-this-in-production-use-256-bit-random-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    ANTHROPIC_API_KEY: str = ""
    CLAUDE_PRIMARY_MODEL: str = "claude-sonnet-4-6"
    CLAUDE_FAST_MODEL: str = "claude-haiku-4-5-20251001"
    CLAUDE_MAX_TOKENS: int = 4096
    CLAUDE_TEMPERATURE: float = 0.1

    LANGCHAIN_API_KEY: str = ""
    LANGCHAIN_TRACING_V2: bool = True
    LANGCHAIN_PROJECT: str = "ai-wealth-manager-india"
    LANGCHAIN_ENDPOINT: str = "https://api.smith.langchain.com"

    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8001
    CHROMA_COLLECTION_NAME: str = "indian_financial_knowledge"
    CHROMA_EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    DEFAULT_INFLATION_RATE: float = 0.06
    DEFAULT_EQUITY_RETURN: float = 0.12
    DEFAULT_DEBT_RETURN: float = 0.07
    DEFAULT_GOLD_RETURN: float = 0.08
    DEFAULT_STEP_UP_RATE: float = 0.10

    BCRYPT_ROUNDS: int = 12

    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "text"

    DEMO_MODE: bool = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
