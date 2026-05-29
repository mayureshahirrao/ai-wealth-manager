"""
main.py — FastAPI application entry point.

Wires together:
- All routers
- Exception handlers
- CORS middleware
- Startup/shutdown lifecycle (DB init, ChromaDB, RAG indexing)
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.error_handler import register_exception_handlers
from app.core.logging_config import setup_logging, get_logger
from app.database.transaction import init_db, close_db

settings = get_settings()
setup_logging(log_level=settings.LOG_LEVEL, log_format=settings.LOG_FORMAT)
logger = get_logger(__name__)


# ─── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("startup_begin", app=settings.APP_NAME, env=settings.APP_ENV)

    # Init database tables
    await init_db()
    logger.info("database_ready")

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
