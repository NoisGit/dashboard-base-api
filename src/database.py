"""
Database configuration and connection management for Locentr API.

This module provides asynchronous database operations using SQLAlchemy.
Schema creation and upgrades are handled exclusively by Alembic.

Key components:
- Async database engine and session configuration
- Session management with proper cleanup
- Connection testing utilities
"""
import logging

from sqlmodel import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.config.config import settings


# Final database URL and debug flag come from central Settings
DATABASE_URL = settings.database_url
DEBUG = settings.debug


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


engine_options = {
    "echo": DEBUG,
    "pool_size": settings.db_pool_size,
    "max_overflow": settings.db_max_overflow,
    "pool_timeout": settings.db_pool_timeout_seconds,
    "pool_recycle": settings.db_pool_recycle_seconds,
    "pool_pre_ping": True,
    "pool_use_lifo": True,
}

if DATABASE_URL and DATABASE_URL.startswith("postgresql"):
    engine_options["connect_args"] = {
        "server_settings": {
            "application_name": "locentr-api",
            "statement_timeout": str(settings.db_statement_timeout_ms),
        }
    }

engine = create_async_engine(DATABASE_URL, **engine_options)


async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session():
    """Async generator that provides a database session."""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def connect_db():
    """Verify the configured database is reachable."""
    try:
        logger.info("Connecting to database...")
        async with engine.connect() as connection:
            await connection.execute(select(1))
        logger.info("Database connection established")
    except Exception as e:
        logger.error("Failed to connect to database: %s", type(e).__name__)
        raise


async def disconnect_db():
    """Dispose the database engine."""
    try:
        logger.info("Disposing database engine...")
        await engine.dispose()
        logger.info("Database engine disposed")
    except Exception:
        logger.error("Error disposing database engine")
        raise


async def test_connection():
    """Test the database connection by executing a simple SELECT statement."""
    try:
        async with async_session() as session:
            await session.execute(select(1))
        return True
    except Exception:  # pylint: disable=broad-except
        logger.error("Database connection test failed")
        return False
