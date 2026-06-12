"""
Application lifespan management module.

This module handles the startup and shutdown events for the FastAPI application,
including database connections and cleanup.
"""
import logging
from contextlib import asynccontextmanager
from src.database import connect_db, disconnect_db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_):
    """Manages the application lifespan events for the FastAPI app."""
    try:
        logger.info("Starting up Locentr API...")
        await connect_db()
    except Exception as e:
        logger.error("Startup failed: %s", str(e))
        raise

    yield

    try:
        logger.info("Shutting down Locentr API...")
        await disconnect_db()
        logger.info("Database disconnected")
    except Exception as e:
        logger.error("Shutdown error: %s", str(e))
