"""
Schemas package for API request and response models.

Exports all Pydantic schema classes used for validating and serializing
API requests and responses across the application.
"""

from .base_schemas import (
    EmptyResponse,
    BaseResponse,
    PaginatedResponse,
    SuccessResponse,
    ErrorResponse,
)
from .audit_log_schema import (
    AuditLogRequest,
    AuditLogResponse,
)
from .user_schemas import (
    UserCreateRequest,
    UserUpdateRequest,
    UserSuspendRequest,
    UserResponse,
    UserMeResponse,
    UserLoginRequest,
    UserChangePasswordRequest,
)
from .company_schemas import (
    CompanyCreateRequest,
    CompanyUpdateRequest,
    CompanyResponse,
    CompanyAssignUserRequest,
    CompanyUserAssignmentResponse,
)
from .location_schemas import (
    LocationCreateRequest,
    LocationUpdateRequest,
    LocationResponse,
    LocationAssignCompanyRequest,
    LocationAssignUserRequest,
    LocationUserAssignmentResponse,
)
from .auth_schemas import (
    AuthRecoveryPasswordRequest,
    AuthResetPasswordRequest,
    AuthTokenResponse,
    RefreshTokenRequest,
    AccessTokenResponse,
)
from .emergency_contact_schemas import (
    EmergencyContactCreateRequest,
    EmergencyContactUpdateRequest,
    EmergencyContactResponse,
)
from .support_ticket_schemas import (
    SupportTicketCreateRequest,
    SupportTicketUpdateRequest,
    SupportTicketResponse,
)
from .notification_schemas import (
    SimpleNoticationRequest,
    NotificationResponse,
    NotificationMessageResponse,
)

__all__ = [
    # Base schemas
    "EmptyResponse",
    "BaseResponse",
    "PaginatedResponse",
    "SuccessResponse",
    "ErrorResponse",
    # Audit log schemas
    "AuditLogRequest",
    "AuditLogResponse",
    # User schemas
    "UserCreateRequest",
    "UserUpdateRequest",
    "UserSuspendRequest",
    "UserResponse",
    "UserMeResponse",
    "UserLoginRequest",
    "UserChangePasswordRequest",
    # Company schemas
    "CompanyCreateRequest",
    "CompanyUpdateRequest",
    "CompanyResponse",
    "CompanyAssignUserRequest",
    "CompanyUserAssignmentResponse",
    # Location schemas
    "LocationCreateRequest",
    "LocationUpdateRequest",
    "LocationResponse",
    "LocationAssignCompanyRequest",
    "LocationAssignUserRequest",
    "LocationUserAssignmentResponse",
    # Auth schemas
    "AuthRecoveryPasswordRequest",
    "AuthResetPasswordRequest",
    "RefreshTokenRequest",
    "AuthTokenResponse",
    "AccessTokenResponse",
    # Emergency contact schemas
    "EmergencyContactCreateRequest",
    "EmergencyContactUpdateRequest",
    "EmergencyContactResponse",
    # Support ticket schemas
    "SupportTicketCreateRequest",
    "SupportTicketUpdateRequest",
    "SupportTicketResponse",
    # Notification schemas
    "SimpleNoticationRequest",
    "NotificationResponse",
    "NotificationMessageResponse",
]
