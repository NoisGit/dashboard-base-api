"""
Schemas package for API request and response models.

Exports all Pydantic schema classes used for validating and serializing
API requests and responses across the application.
"""

from .access_log_schemas import (
    AccessLogCreateRequest,
    AccessLogExitRequest,
    AccessLogBulkExitRequest,
    AccessLogResponse,
    ExternalPeopleResponse,
)
from .audit_log_schema import (
    AuditLogRequest,
    AuditLogResponse,
)
from .auth_schemas import (
    AccessTokenResponse,
    AuthRecoveryPasswordRequest,
    AuthResetPasswordRequest,
    AuthTokenResponse,
    RefreshTokenRequest,
)
from .azure_schemas import (
    AzureDeleteRequest,
    AzureDeleteResponse,
    AzureResponse,
    AzureUpdateRequest,
    AzureUpdateResponse,
    AzureUploadRequest,
)
from .base_schemas import (
    BaseResponse,
    EmptyResponse,
    ErrorResponse,
    PaginatedResponse,
    SuccessResponse,
)
from .blacklist_schemas import (
    BlacklistCreateRequest,
    BlacklistResponse,
)
from .company_schemas import (
    CompanyAssignUserRequest,
    CompanyCreateRequest,
    SubCompanyCreateRequest,
    CompanyResponse,
    CompanyUpdateRequest,
    CompanyUserAssignmentResponse,
)
from .dashboard_schemas import (
    ChartStatsResponse,
    DashboardStatsResponse,
    EntriesByMonthResponse,
    GenderDistributionResponse,
    KpisBlacklistResponse,
    KpisResponse,
    KpisWhitelistResponse,
    RecentEntriesResponse,
)
from .document_schemas import (
    DocumentCreateRequest,
    DocumentDownloadResponse,
    DocumentResponse,
    DocumentUpdateRequest,
)
from .emergency_contact_schemas import (
    EmergencyContactCreateRequest,
    EmergencyContactResponse,
    EmergencyContactUpdateRequest,
)
from .location_schemas import (
    LocationAssignCompanyRequest,
    LocationAssignUserRequest,
    LocationCreateRequest,
    LocationResponse,
    LocationUpdateRequest,
    LocationUserAssignmentResponse,
)
from .notification_schemas import (
    NotificationMessageResponse,
    NotificationResponse,
    SimpleNoticationRequest,
)
from .service_contact_schemas import (
    ServiceContactCreateRequest,
    ServiceContactResponse,
    ServiceContactUpdateRequest,
)
from .support_ticket_schemas import (
    SupportTicketCommentCreateRequest,
    SupportTicketCommentResponse,
    SupportTicketCommentUpdateRequest,
    SupportTicketCreateRequest,
    SupportTicketResponse,
    SupportTicketUpdateRequest,
)
from .system_schemas import (
    AdminDetailResponse,
    DetailAdminsResponse,
    MonthlyIncomeResponse,
    StatsDataResponse,
    SystemCountersResponse,
    SystemStatsResponse,
)
from .user_schemas import (
    UserChangePasswordRequest,
    UserCreateRequest,
    UserLoginRequest,
    UserMeResponse,
    UserResponse,
    UserSuspendRequest,
    UserUpdateRequest,
)
from .whitelist_schemas import (
    WhitelistCreateRequest,
    WhitelistResponse,
)
from .location_logbook_schemas import (
    LocationLogbookMediaType,
    LocationLogbookCreateRequest,
    LocationLogbookResponse,
    LocationLogbookSettingsUpdateRequest,
    LocationLogbookSettingsResponse,
    PoliceAccessCreateRequest,
    PoliceLinkResponse,
    PoliceViewResponse,
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
    "SubCompanyCreateRequest",
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
    # Whitelist schemas
    "WhitelistCreateRequest",
    "WhitelistResponse",
    # Blacklist schemas
    "BlacklistCreateRequest",
    "BlacklistResponse",
    # Emergency contact schemas
    "EmergencyContactCreateRequest",
    "EmergencyContactUpdateRequest",
    "EmergencyContactResponse",
    # Support ticket schemas
    "SupportTicketCreateRequest",
    "SupportTicketUpdateRequest",
    "SupportTicketResponse",
    "SupportTicketCommentCreateRequest",
    "SupportTicketCommentUpdateRequest",
    "SupportTicketCommentResponse",
    # Service contact schemas
    "ServiceContactCreateRequest",
    "ServiceContactUpdateRequest",
    "ServiceContactResponse",
    # Notification schemas
    "SimpleNoticationRequest",
    "NotificationResponse",
    "NotificationMessageResponse",
    # System schemas
    "SystemStatsResponse",
    "SystemCountersResponse",
    "MonthlyIncomeResponse",
    "AdminDetailResponse",
    "StatsDataResponse",
    "DetailAdminsResponse",
    # Access log schemas
    "AccessLogCreateRequest",
    "AccessLogExitRequest",
    "AccessLogBulkExitRequest",
    "AccessLogResponse",
    "ExternalPeopleResponse",
    # Azure schemas
    "AzureUploadRequest",
    "AzureUpdateRequest",
    "AzureDeleteRequest",
    "AzureResponse",
    "AzureUpdateResponse",
    "AzureDeleteResponse",
    # Document schemas
    "DocumentCreateRequest",
    "DocumentUpdateRequest",
    "DocumentResponse",
    "DocumentDownloadResponse",
    # Dashboard schemas
    "KpisResponse",
    "KpisWhitelistResponse",
    "KpisBlacklistResponse",
    "EntriesByMonthResponse",
    "DashboardStatsResponse",
    "GenderDistributionResponse",
    "ChartStatsResponse",
    "RecentEntriesResponse",
    # Location logbook schemas
    "LocationLogbookMediaType",
    "LocationLogbookCreateRequest",
    "LocationLogbookResponse",
    "LocationLogbookSettingsUpdateRequest",
    "LocationLogbookSettingsResponse",
    "PoliceAccessCreateRequest",
    "PoliceLinkResponse",
    "PoliceViewResponse",
]
