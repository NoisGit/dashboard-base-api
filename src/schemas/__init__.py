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
    UserResponse,
    UserMeResponse,
    UserLoginRequest,
    UserTokenResponse,
    RefreshTokenRequest,
    AccessTokenResponse,
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
    "UserResponse",
    "UserMeResponse",
    "UserLoginRequest",
    "UserTokenResponse",
    "RefreshTokenRequest",
    "AccessTokenResponse",
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
]
