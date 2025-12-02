"""Dependency injection configuration for Sentinel Enterprise API."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.services.user_service import UserService


def get_user_service(
    session: AsyncSession = Depends(get_session),
) -> UserService:
    """Dependency to get a UserService instance."""
    return UserService(session)
