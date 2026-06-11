"""
Database configuration and connection management for Locentr API.

This module provides asynchronous database operations using SQLModel and SQLAlchemy.
It handles database engine creation, session management, table creation, and connection
testing for the relational database.

Key components:
- Async database engine and session configuration
- Database initialization and table creation
- Session management with proper cleanup
- Connection testing utilities
"""
import logging

from sqlmodel import SQLModel, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.config.config import settings
from src.models import __all__ as models  # noqa: F401  # force models import


# Final database URL and debug flag come from central Settings
DATABASE_URL = settings.database_url
DEBUG = settings.debug


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


engine = create_async_engine(
    DATABASE_URL,
    echo=DEBUG,
    pool_recycle=1800,
    pool_pre_ping=True,
)


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


async def create_db_and_tables():
    """Create all tables defined in SQLModel metadata."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def connect_db():
    """Initialize the database by creating tables, if needed."""
    try:
        logger.info("🔄 Initializing database...")
        await create_db_and_tables()
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error("❌ Failed to initialize database: %s", type(e).__name__)
        raise


async def disconnect_db():
    """Dispose the database engine."""
    try:
        logger.info("🔄 Disposing database engine...")
        await engine.dispose()
        logger.info("✅ Database engine disposed")
    except Exception:
        logger.error("❌ Error disposing database engine")
        raise


async def test_connection():
    """Test the database connection by executing a simple SELECT statement."""
    try:
        async with async_session() as session:
            await session.execute(select(1))
        return True
    except Exception:  # pylint: disable=broad-except
        logger.error("❌ Database connection test failed")
        return False
