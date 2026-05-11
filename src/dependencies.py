"""Dependency injection configuration for Coredeck API."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.services.access_log_service import AccessLogService
from src.services.audit_log_service import AuditLogService
from src.services.auth_service import AuthService
from src.services.storage_service import StorageService
from src.services.blacklist_service import BlacklistService
from src.services.company_service import CompanyService
from src.services.dashboard_service import DashboardService
from src.services.document_service import DocumentService
from src.services.email_service import EmailService
from src.services.emergency_contact_service import EmergencyContactService
from src.services.location_logbook_service import LocationLogbookService
from src.services.location_service import LocationService
from src.services.notification_service import NotificationService
from src.services.service_contact_service import ServiceContactService
from src.services.support_ticket_service import SupportTicketService
from src.services.system_service import SystemService
from src.services.user_service import UserService
from src.services.whitelist_service import WhitelistService


def get_storage_service() -> StorageService:
    """Dependency to get a StorageService instance."""
    return StorageService()


def get_audit_log_service(
    session: AsyncSession = Depends(get_session),
) -> AuditLogService:
    """Dependency to get an AuditLogService instance."""
    return AuditLogService(session)


def get_email_service() -> EmailService:
    """Dependency to get an EmailService instance."""
    return EmailService()


def get_auth_service(
    session: AsyncSession = Depends(get_session),
    email_service: EmailService = Depends(get_email_service),
) -> AuthService:
    """Dependency to get an AuthService instance."""
    return AuthService(email_service, session)


def get_user_service(
    session: AsyncSession = Depends(get_session),
) -> UserService:
    """Dependency to get a UserService instance."""
    return UserService(session)


def get_company_service(
    session: AsyncSession = Depends(get_session),
    user_service: UserService = Depends(get_user_service),
    storage_service: StorageService = Depends(get_storage_service),
) -> CompanyService:
    """Dependency to get a CompanyService instance."""
    return CompanyService(session, user_service, storage_service)


def get_location_service(
    session: AsyncSession = Depends(get_session),
    user_service: UserService = Depends(get_user_service),
    company_service: CompanyService = Depends(get_company_service),
    storage_service: StorageService = Depends(get_storage_service),
) -> LocationService:
    """Dependency to get a LocationService instance."""
    return LocationService(session, storage_service, user_service, company_service)


def get_location_logbook_service(
    session: AsyncSession = Depends(get_session),
    storage_service: StorageService = Depends(get_storage_service),
    location_service: LocationService = Depends(get_location_service),
) -> LocationLogbookService:
    """Dependency to get a LocationLogbookService instance."""
    return LocationLogbookService(session, storage_service, location_service)


def get_emergency_contact_service(
    session: AsyncSession = Depends(get_session),
    user_service: UserService = Depends(get_user_service),
    location_service: LocationService = Depends(get_location_service),
) -> EmergencyContactService:
    """Dependency to get an EmergencyContactService instance."""
    return EmergencyContactService(session, user_service, location_service)


def get_service_contact_service(
    session: AsyncSession = Depends(get_session),
    user_service: UserService = Depends(get_user_service),
    location_service: LocationService = Depends(get_location_service),
) -> ServiceContactService:
    """Dependency to get a ServiceContactService instance."""
    return ServiceContactService(session, user_service, location_service)


def get_support_ticket_service(
    session: AsyncSession = Depends(get_session),
    user_service: UserService = Depends(get_user_service),
    storage_service: StorageService = Depends(get_storage_service),
) -> SupportTicketService:
    """Dependency to get a SupportTicketService instance."""
    return SupportTicketService(session, user_service, storage_service)


def get_notification_service(
    session: AsyncSession = Depends(get_session),
    user_service: UserService = Depends(get_user_service),
) -> NotificationService:
    """Dependency to get a NotificationService instance."""
    return NotificationService(session, user_service)


def get_whitelist_service(
    session: AsyncSession = Depends(get_session),
    user_service: UserService = Depends(get_user_service),
    location_service: LocationService = Depends(get_location_service),
) -> WhitelistService:
    """Dependency to get a WhitelistService instance."""
    return WhitelistService(session, user_service, location_service)


def get_blacklist_service(
    session: AsyncSession = Depends(get_session),
    user_service: UserService = Depends(get_user_service),
    location_service: LocationService = Depends(get_location_service),
) -> BlacklistService:
    """Dependency to get a BlacklistService instance."""
    return BlacklistService(session, user_service, location_service)


def get_system_service(
    session: AsyncSession = Depends(get_session),
) -> SystemService:
    """Dependency to get a SystemService instance."""
    return SystemService(session)


def get_access_log_service(
    session: AsyncSession = Depends(get_session),
    storage_service: StorageService = Depends(get_storage_service),
    user_service: UserService = Depends(get_user_service),
    location_service: LocationService = Depends(get_location_service),
) -> AccessLogService:
    """Dependency to get an AccessLogService instance."""
    return AccessLogService(session, storage_service, user_service, location_service)


def get_document_service(
    session: AsyncSession = Depends(get_session),
    user_service: UserService = Depends(get_user_service),
    storage_service: StorageService = Depends(get_storage_service),
) -> DocumentService:
    """Dependency to get a DocumentService instance."""
    return DocumentService(session, user_service, storage_service)


def get_dashboard_service(
    session: AsyncSession = Depends(get_session),
    user_service: UserService = Depends(get_user_service),
    location_service: LocationService = Depends(get_location_service),
) -> DashboardService:
    """Dependency to get a DashboardService instance."""
    return DashboardService(session, user_service, location_service)
