"""
config.py — Centralized application configuration via pydantic-settings.

All environment variables are loaded here once. Use get_settings() everywhere
instead of os.getenv(). The lru_cache means settings are loaded exactly once.

Dependencies: None (Tier 1 — external lib only)
Consumed by: All backend modules
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ─── Application ───────────────────────────────────────────────────────
    APP_NAME: str = "AI Wealth Manager"
    APP_ENV: str = "development"        # development | staging | production
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # ─── Database ──────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://wealth:wealth@localhost:5432/wealth_manager"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_ECHO: bool = False        # Set True to log all SQL queries

    # ─── JWT Authentication ────────────────────────────────────────────────
    JWT_SECRET_KEY: str = "change-this-in-production-use-256-bit-random-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hours (demo session)

    # ─── Anthropic / Claude ────────────────────────────────────────────────
    ANTHROPIC_API_KEY: str = ""
    CLAUDE_PRIMARY_MODEL: str = "claude-sonnet-4-6"       # Complex reasoning
    CLAUDE_FAST_MODEL: str = "claude-haiku-4-5-20251001"  # Quick lookups
    CLAUDE_MAX_TOKENS: int = 4096
    CLAUDE_TEMPERATURE: float = 0.1   # Low temperature for financial advice

    # ─── LangSmith (Observability) ─────────────────────────────────────────
    LANGCHAIN_API_KEY: str = ""
    LANGCHAIN_TRACING_V2: bool = True
    LANGCHAIN_PROJECT: str = "ai-wealth-manager-india"
    LANGCHAIN_ENDPOINT: str = "https://api.smith.langchain.com"

    # ─── ChromaDB (Vector Store) ───────────────────────────────────────────
    CHROMA_HOST: str = "chromadb"
    CHROMA_PORT: int = 8001
    CHROMA_COLLECTION_NAME: str = "indian_financial_knowledge"
    CHROMA_EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    # ─── Indian Financial Defaults ─────────────────────────────────────────
    DEFAULT_INFLATION_RATE: float = 0.06     # 6% India CPI
    DEFAULT_EQUITY_RETURN: float = 0.12      # 12% Nifty 50 long-term CAGR
    DEFAULT_DEBT_RETURN: float = 0.07        # 7% debt MF return
    DEFAULT_GOLD_RETURN: float = 0.08        # 8% gold long-term
    DEFAULT_STEP_UP_RATE: float = 0.10       # 10% annual SIP step-up

    # ─── Security ──────────────────────────────────────────────────────────
    BCRYPT_ROUNDS: int = 12

    # ─── Logging ───────────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"    # json | text

    # ─── Demo Mode ─────────────────────────────────────────────────────────
    DEMO_MODE: bool = True      # Enables demo client seeding + mock market data


@lru_cache()
def get_settings() -> Settings:
    """
    Returns cached Settings instance. Called once at startup.

    Usage:
        from skills.backend.core.config import get_settings
        settings = get_settings()
        api_key = settings.ANTHROPIC_API_KEY
    """
    return Settings()
