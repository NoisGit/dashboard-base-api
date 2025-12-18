"""Dependency injection configuration for Sentinel Enterprise API."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.services.audit_log_service import AuditLogService
from src.services.auth_service import AuthService
from src.services.user_service import UserService
from src.services.email_service import EmailService
from src.services.company_service import CompanyService
from src.services.location_service import LocationService
from src.services.emergency_contact_service import EmergencyContactService
from src.services.support_ticket_service import SupportTicketService


def get_audit_log_service(
    session: AsyncSession = Depends(get_session),
) -> AuditLogService:
    """Dependency to get an AuditLogService instance."""
    return AuditLogService(session)


def get_email_service() -> EmailService:
    """Dependency to get EmailService instance"""
    return EmailService()


def get_auth_service(
    session: AsyncSession = Depends(get_session),
    email_service: EmailService = Depends(get_email_service),
) -> AuthService:
    """Dependency to get a AuthService instance."""
    return AuthService(email_service, session)


def get_user_service(
    session: AsyncSession = Depends(get_session),
) -> UserService:
    """Dependency to get a UserService instance."""
    return UserService(session)


def get_company_service(
    session: AsyncSession = Depends(get_session),
    user_service: UserService = Depends(get_user_service),
) -> CompanyService:
    """Dependency to get a CompanyService instance."""
    return CompanyService(session, user_service)


def get_location_service(
    session: AsyncSession = Depends(get_session),
    user_service: UserService = Depends(get_user_service),
) -> LocationService:
    """Dependency to get a LocationService instance."""
    return LocationService(session, user_service)


def get_emergency_contact_service(
    session: AsyncSession = Depends(get_session),
    user_service: UserService = Depends(get_user_service),
) -> EmergencyContactService:
    """Dependency to get an EmergencyContactService instance."""
    return EmergencyContactService(session, user_service)


def get_support_ticket_service(
    session: AsyncSession = Depends(get_session),
) -> SupportTicketService:
    """Dependency to get a SupportTicketService instance"""
    return SupportTicketService(session)
