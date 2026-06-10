"""
Quant AI Agent — Database Session Factory

Provides async SQLAlchemy engine and session for PostgreSQL + TimescaleDB.
Uses connection pooling for production performance.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings

settings = get_settings()

# Create async engine with connection pooling
engine = create_async_engine(
    settings.database_url,
    echo=settings.log_level == "DEBUG",
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600,    # Recycle connections after 1 hour
)

# Session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides a database session.

    Usage:
        @router.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database connection on app startup.
    Tables are created by the SQL init script, not by SQLAlchemy.
    This just verifies connectivity.
    """
    async with engine.begin() as conn:
        # Simple connectivity check
        await conn.execute(
            __import__("sqlalchemy").text("SELECT 1")
        )


async def close_db() -> None:
    """Dispose engine connections on app shutdown."""
    await engine.dispose()
