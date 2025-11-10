"""
Database configuration and connection management for Sentinel Enterprise API.

This module provides asynchronous database operations using SQLModel and SQLAlchemy.
It handles database engine creation, session management, table creation, and connection
testing for the PostgreSQL database.

Key components:
- Async database engine and session configuration
- Database initialization and table creation
- Session management with proper cleanup
- Connection testing utilities
"""
import os
import logging
from sqlmodel import SQLModel, select
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.models import __all__ as models

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


DATABASE_URL = os.getenv("DATABASE_URL")
DEBUG = os.getenv("DEBUG", "False").lower() == "True"

if not DATABASE_URL:
    raise ValueError("❌ DATABASE_URL environment variable is required")

engine = create_async_engine(
    DATABASE_URL,
    echo=DEBUG,
    pool_recycle=1800,
    pool_pre_ping=True,
)
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_session():
    """Asynchronous generator function that provides a database session."""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def create_db_and_tables():
    """Asynchronously creates the database and all tables defined in the SQLModel metadata."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def connect_db():
    """Asynchronously initializes the database by creating necessary tables."""
    try:
        logger.info("🔄 Initializing database...")
        await create_db_and_tables()
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error("❌ Failed to initialize database: %s", type(e).__name__)
        raise


async def disconnect_db():
    """Asynchronously disposes of the database engine."""
    try:
        logger.info("🔄 Disposing database engine...")
        await engine.dispose()
        logger.info("✅ Database engine disposed")
    except Exception:
        logger.error("❌ Error disposing database engine")
        raise


async def test_connection():
    """Asynchronously tests the database connection by executing a simple SELECT statement."""
    try:
        async with async_session() as session:
            await session.execute(select(1))
        return True
    except Exception:
        logger.error("❌ Database connection test failed")
        return False
