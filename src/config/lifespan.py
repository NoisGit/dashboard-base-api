"""
Application lifespan management module.

This module handles the startup and shutdown events for the FastAPI application,
including database connections and cleanup.
"""
import logging
from contextlib import asynccontextmanager
from src.database import connect_db, disconnect_db, test_connection

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_):
    """Manages the application lifespan events for the FastAPI app."""
    try:
        logger.info("🚀 Starting up Coredeck API...")
        await connect_db()

        if await test_connection():
            logger.info("✅ Database connection tested successfully")
        else:
            logger.warning("⚠️ Database connection test failed")
    except Exception as e:
        logger.error("❌ Startup failed: %s", str(e))
        raise e

    yield

    try:
        logger.info("🛑 Shutting down Coredeck API...")
        await disconnect_db()
        logger.info("✅ Database disconnected")
    except Exception as e:
        logger.error("❌ Shutdown error: %s", str(e))
