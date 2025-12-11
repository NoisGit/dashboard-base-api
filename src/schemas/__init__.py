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

from .user_schemas import (
    UserCreateRequest,
    UserUpdateRequest,
    UserResponse,
    UserLoginRequest,
    UserTokenResponse,
    RefreshTokenRequest,
    AccessTokenResponse,
    StatusResponse,
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
    # User schemas
    "UserCreateRequest",
    "UserUpdateRequest",
    "UserResponse",
    "UserLoginRequest",
    "UserTokenResponse",
    "RefreshTokenRequest",
    "AccessTokenResponse",
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
