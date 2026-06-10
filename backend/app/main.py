"""
main.py — FastAPI application entry point.

Wires together:
- All routers
- Exception handlers
- CORS middleware
- Rate limiting (slowapi) — AI endpoints: 10/min per IP
- Startup/shutdown lifecycle (DB init, ChromaDB, RAG indexing)
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import get_settings
from app.core.error_handler import register_exception_handlers
from app.core.logging_config import setup_logging, get_logger
from app.database.transaction import init_db, close_db
from app.ai.langsmith_tracer import setup_langsmith

settings = get_settings()
setup_logging(log_level=settings.LOG_LEVEL, log_format=settings.LOG_FORMAT)
logger = get_logger(__name__)

# ─── Rate Limiter (shared — imported by routers that need per-route limits) ───
limiter = Limiter(key_func=get_remote_address, default_limits=["300/minute"])


# ─── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("startup_begin", app=settings.APP_NAME, env=settings.APP_ENV)

    # Init database tables
    await init_db()
    logger.info("database_ready")

    # Configure LangSmith tracing (no-op if key not set)
    setup_langsmith()

    yield  # App runs here

    await close_db()
    logger.info("shutdown_complete")


# ─── App Instance ──────────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-Powered Wealth Management Platform — Indian Context",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ─── Rate Limiting Middleware ──────────────────────────────────────────────────

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# ─── CORS ──────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Exception Handlers ────────────────────────────────────────────────────────

register_exception_handlers(app)

# ─── Routers ───────────────────────────────────────────────────────────────────

from app.auth.router import router as auth_router
from app.api.clients import router as clients_router
from app.api.me import router as me_router
from app.api.chat import router as chat_router
from app.api.rm import router as rm_router
from app.api.compliance import router as compliance_router
from app.api.financial_plan import router as financial_plan_router
from app.api.market import router as market_router

app.include_router(auth_router)
app.include_router(clients_router)
app.include_router(me_router)
app.include_router(chat_router)
app.include_router(rm_router)
app.include_router(compliance_router)
app.include_router(financial_plan_router)
app.include_router(market_router)


# ─── Health Check ──────────────────────────────────────────────────────────────

@app.get("/health", tags=["system"])
async def health():
    return {"status": "ok", "version": settings.APP_VERSION, "env": settings.APP_ENV}
