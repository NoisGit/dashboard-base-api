"""Access Logs Router for Sentinel Enterprise API."""

from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, Query, status
from fastapi_pagination import Page, Params

from src.auth.utils import get_current_user
from src.auth.permissions import RoleChecker
from src.core.enums import UserRole
from src.dependencies import get_access_log_service
from src.schemas.access_log_schemas import (
    AccessLogCreateRequest,
    AccessLogExitRequest,
    AccessLogBulkExitRequest,
    AccessLogResponse,
)
from src.schemas import EmptyResponse
from src.services.access_log_service import AccessLogService


router = APIRouter(prefix="/access-logs", tags=["access-logs"])


@router.get(
    "/guard/active/{location_id}",
    response_model=List[AccessLogResponse],
)
async def get_active_entries(
    location_id: int,
    service: AccessLogService = Depends(get_access_log_service),
    user_id: int = Depends(RoleChecker([
        UserRole.JANITOR,
        UserRole.SUBADMIN,
        UserRole.ADMIN,
        UserRole.SUPERADMIN
    ])),
) -> List[AccessLogResponse]:
    """
    Get active access logs for a specific location.
    Active = persons who have entered but not yet exited.
    """
    return await service.get_active_entries(location_id, user_id)


@router.get(
    "/guard/exits-today/{location_id}",
    response_model=List[AccessLogResponse],
)
async def get_today_exits(
    location_id: int,
    service: AccessLogService = Depends(get_access_log_service),
    user_id: int = Depends(RoleChecker([
        UserRole.JANITOR,
        UserRole.SUBADMIN,
        UserRole.ADMIN,
        UserRole.SUPERADMIN
    ])),
) -> List[AccessLogResponse]:
    """
    Get access logs with exits from today for a specific location.
    """
    return await service.get_today_exits(location_id, user_id)


@router.post(
    "/",
    response_model=AccessLogResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_access_log(
    payload: AccessLogCreateRequest,
    service: AccessLogService = Depends(get_access_log_service),
    user_id=Depends(RoleChecker([UserRole.JANITOR])),
) -> AccessLogResponse:
    """
    Create a new access log entry (person entering).
    Only JANITOR (guard) can create entries.
    """
    return await service.create_access_log(
        payload=payload,
        created_by=user_id,
    )


@router.patch(
    "/{access_log_id}/exit",
    response_model=AccessLogResponse,
)
async def register_exit(
    access_log_id: int,
    payload: AccessLogExitRequest,
    service: AccessLogService = Depends(get_access_log_service),
    user_id=Depends(RoleChecker([UserRole.JANITOR])),
) -> AccessLogResponse:
    """
    Register exit for an existing access log.
    Only JANITOR (guard) can register exits.
    """
    return await service.register_exit(
        access_log_id=access_log_id,
        payload=payload,
        exit_created_by=user_id,
    )


@router.patch(
    "/dashboard/{access_log_id}/exit",
    response_model=EmptyResponse,
)
async def register_exit_dashboard(
    access_log_id: int,
    payload: AccessLogExitRequest,
    service: AccessLogService = Depends(get_access_log_service),
    user_id=Depends(RoleChecker([
        UserRole.SUBADMIN,
        UserRole.ADMIN,
        UserRole.SUPERADMIN
    ])),
    current_user=Depends(get_current_user),
) -> EmptyResponse:
    """
    Register exit for an existing access log from dashboard.
    Only Admin roles can register exits.
    """
    role_str = current_user.get("role")
    enforce_location_access = role_str != UserRole.SUPERADMIN.value

    return await service.register_exit_admin(
        access_log_id=access_log_id,
        payload=payload,
        exit_created_by=user_id,
        enforce_location_access=enforce_location_access,
    )


@router.patch(
    "/dashboard/exit/bulk",
    response_model=EmptyResponse,
)
async def register_exit_bulk_dashboard(
    payload: AccessLogBulkExitRequest,
    service: AccessLogService = Depends(get_access_log_service),
    user_id=Depends(RoleChecker([
        UserRole.SUBADMIN,
        UserRole.ADMIN,
        UserRole.SUPERADMIN
    ])),
    current_user=Depends(get_current_user),
) -> EmptyResponse:
    """
    Register exits in bulk from dashboard.
    Only Admin roles can register exits.
    """
    role_str = current_user.get("role")
    enforce_location_access = role_str != UserRole.SUPERADMIN.value

    return await service.register_exit_bulk_admin(
        payload=payload,
        exit_created_by=user_id,
        enforce_location_access=enforce_location_access,
    )


@router.get(
    "/dashboard/{location_id}",
    response_model=Page[AccessLogResponse],
)
async def get_logs_dashboard(  # pylint: disable=too-many-arguments, too-many-positional-arguments
    location_id: int,
    params: Params = Depends(),
    start_date: Optional[datetime] = Query(
        default=None,
        description="Filter logs created after this date (ISO format)",
    ),
    end_date: Optional[datetime] = Query(
        default=None,
        description="Filter logs created before this date (ISO format)",
    ),
    status_filter: Optional[str] = Query(
        default=None,
        alias="status",
        description="Filter by status: 'active', 'completed', or 'all'",
        regex="^(active|completed|all)$",
    ),
    search_plate: Optional[str] = Query(
        default=None,
        description="Search by vehicle plate",
    ),
    search_name: Optional[str] = Query(
        default=None,
        description="Search by person name",
    ),
    search_dni: Optional[str] = Query(
        default=None,
        description="Search by person DNI",
    ),
    service: AccessLogService = Depends(get_access_log_service),
    user_id: int = Depends(RoleChecker([
        UserRole.CLIENT,
        UserRole.SUBADMIN,
        UserRole.ADMIN,
        UserRole.SUPERADMIN
    ])),
) -> Page[AccessLogResponse]:
    """
    Get access logs with pagination and filters for dashboard.
    Filters by a specific location.
    """
    return await service.get_logs_paginated(
        location_id=location_id,
        user_id=user_id,
        params=params,
        start_date=start_date,
        end_date=end_date,
        status_filter=status_filter,
        search_plate=search_plate,
        search_name=search_name,
        search_dni=search_dni,
    )
