"""
Models package for the Coredeck API.

This package contains all the data models and entities used throughout the application.

All models are imported and made available through this package's public interface
via the __all__ list.
"""

from src.core.enums import UserRole

from .plan import Plan
from .company import Company
from .location import Location
from .user import User
from .user_location_access import UserLocationAccess
from .company_location_access import CompanyLocationAccess
from .company_staff import CompanyStaff
from .custom_form import CustomForm
from .custom_form_field import CustomFormField
from .emergency_contact import EmergencyContact
from .type_access_list import TypeAccessList
from .access_list import AccessList
from .external_people import ExternalPeople
from .access_log import AccessLog, AccessLogImage
from .document import Document
from .support_ticket import SupportTicket
from .support_response import SupportResponse
from .audit_log import AuditLog
from .service_contacts import ServiceContact
from .notification import Notification
from .location_logbook import LocationLogbook, LocationLogbookSettings, PoliceAccessPermit


__all__ = [
    "Plan",
    "Company",
    "Location",
    "User",
    "UserRole",
    "UserLocationAccess",
    "CompanyLocationAccess",
    "CompanyStaff",
    "CustomForm",
    "CustomFormField",
    "EmergencyContact",
    "TypeAccessList",
    "AccessList",
    "ExternalPeople",
    "AccessLog",
    "AccessLogImage",
    "Document",
    "SupportTicket",
    "SupportResponse",
    "AuditLog",
    "ServiceContact",
    "Notification",
    "LocationLogbook",
    "LocationLogbookSettings",
    "PoliceAccessPermit",
]
