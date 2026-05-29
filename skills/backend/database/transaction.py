"""
transaction.py — Async database session and unit-of-work management.

Provides:
1. get_db() — FastAPI dependency for injecting an async session per request
2. transactional() — decorator for service methods that need atomic operations

Dependencies: config.py, base_model.py (Tier 4)
Consumed by: All route handlers (via Depends), multi-step service operations
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from skills.backend.core.config import get_settings
from skills.backend.core.logging_config import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Engine is created once at module load
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    echo=settings.DATABASE_ECHO,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Don't expire objects after commit (safer in async)
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency: provides an async DB session per request.
    Automatically commits on success, rolls back on exception.

    Usage in routes:
        @router.get("/clients")
        async def get_clients(db: AsyncSession = Depends(get_db)):
            repo = ClientRepository(Client, db)
            return await repo.get_all()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as exc:
            await session.rollback()
            logger.error("db_session_error", error=str(exc))
            raise


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for DB sessions outside of request scope.
    Use for background tasks, seeding scripts, and scheduled jobs.

    Usage:
        async with get_db_context() as db:
            repo = ClientRepository(Client, db)
            client = await repo.create({...})
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as exc:
            await session.rollback()
            logger.error("db_context_error", error=str(exc))
            raise


async def init_db() -> None:
    """
    Create all tables. Called at application startup in main.py.
    In production, use Alembic migrations instead.
    """
    from skills.backend.database.base_model import WealthBase
    async with engine.begin() as conn:
        await conn.run_sync(WealthBase.metadata.create_all)
    logger.info("database_initialized")


async def close_db() -> None:
    """Dispose connection pool. Called at application shutdown."""
    await engine.dispose()
    logger.info("database_connection_pool_closed")
