"""Dependency injection configuration for Sentinel Enterprise API."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.services.user_service import UserService
from src.services.company_service import CompanyService
from src.services.location_service import LocationService


def get_user_service(
    session: AsyncSession = Depends(get_session),
) -> UserService:
    """Dependency to get a UserService instance."""
    return UserService(session)


def get_company_service(
    session: AsyncSession = Depends(get_session),
) -> CompanyService:
    """Dependency to get a CompanyService instance."""
    return CompanyService(session)


def get_location_service(
    session: AsyncSession = Depends(get_session),
) -> LocationService:
    """Dependency to get a LocationService instance."""
    return LocationService(session)
