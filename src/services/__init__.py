"""
Service module initialization.

This module centralizes the export of core service classes used for
business logic and database operations in the Coredeck API.
"""

import sys

from .auth_service import AuthService
from .storage_service import StorageService
from . import storage_service as _storage_service_module

# Temporary import compatibility while large services finish migrating to StorageService.
AzureService = StorageService
_storage_service_module.AzureService = StorageService
sys.modules[__name__ + ".azure_service"] = _storage_service_module

from .user_service import UserService
from .company_service import CompanyService
from .location_service import LocationService
from .email_service import EmailService
from .emergency_contact_service import EmergencyContactService
from .support_ticket_service import SupportTicketService
from .service_contact_service import ServiceContactService
from .whitelist_service import WhitelistService
from .blacklist_service import BlacklistService
from .system_service import SystemService
from .location_logbook_service import LocationLogbookService
from .document_service import DocumentService

__all__ = [
    "AuthService",
    "StorageService",
    "AzureService",
    "UserService",
    "CompanyService",
    "LocationService",
    "EmailService",
    "EmergencyContactService",
    "SupportTicketService",
    "ServiceContactService",
    "WhitelistService",
    "BlacklistService",
    "SystemService",
    "LocationLogbookService",
    "DocumentService",
]
