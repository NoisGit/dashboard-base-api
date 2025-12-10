"""Locations router module for Sentinel Enterprise API."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from fastapi_pagination import Page, paginate

from src.auth.utils import get_user_data_from_token
from src.auth.permissions import RoleChecker
from src.core.enums import UserRole
from src.dependencies import get_location_service
from src.schemas import (
    LocationCreateRequest,
    LocationUpdateRequest,
    LocationResponse,
    LocationAssignCompanyRequest,
    LocationAssignUserRequest,
    LocationUserAssignmentResponse,
)
from src.services.location_service import LocationService

router = APIRouter(
    prefix="/locations",
    tags=["locations"],
)


@router.get(
    "/",
    response_model=Page[LocationResponse],
)
async def list_locations(
    company_id: Optional[int] = Query(default=None),
    search: Optional[str] = Query(default=None),
    service: LocationService = Depends(get_location_service),
    current_user_data: tuple[int, UserRole] = Depends(
        get_user_data_from_token),
) -> Page[LocationResponse]:
    """List active locations (porterías) visible for the current user."""
    user_id, role = current_user_data

    locations = await service.list_locations(
        user_id=user_id,
        role=role,
        company_id=company_id,
        search=search,
    )
    return paginate(locations)


@router.get(
    "/{location_id}",
    response_model=LocationResponse,
)
async def get_location_detail(
    location_id: int,
    service: LocationService = Depends(get_location_service),
    current_user_data: tuple[int, UserRole] = Depends(
        get_user_data_from_token),
) -> LocationResponse:
    """Get a single active location by ID."""
    user_id, role = current_user_data

    location = await service.get_location_detail(
        user_id=user_id,
        role=role,
        location_id=location_id,
    )
    return location


@router.post(
    "/",
    response_model=LocationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_location(
    payload: LocationCreateRequest,
    service: LocationService = Depends(get_location_service),
    current_user_data: tuple[int, UserRole] = Depends(
        RoleChecker([UserRole.SUPERADMIN, UserRole.ADMIN]),
    ),
) -> LocationResponse:
    """Create a new location (portería)."""
    user_id, _ = current_user_data

    location = await service.create_location(
        user_id=user_id,
        payload=payload,
    )
    return location


@router.put(
    "/{location_id}",
    response_model=LocationResponse,
)
async def update_location(
    location_id: int,
    payload: LocationUpdateRequest,
    service: LocationService = Depends(get_location_service),
    current_user_data: tuple[int, UserRole] = Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
                UserRole.ADMIN,
                UserRole.SUBADMIN,
            ],
        ),
    ),
) -> LocationResponse:
    """Update an existing location."""
    user_id, role = current_user_data

    location = await service.update_location(
        user_id=user_id,
        role=role,
        location_id=location_id,
        payload=payload,
    )
    return location


@router.delete(
    "/{location_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_location(
    location_id: int,
    service: LocationService = Depends(get_location_service),
    current_user_data: tuple[int, UserRole] = Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
                UserRole.ADMIN,
            ],
        ),
    ),
):
    """Soft delete a location (is_active = False)."""
    user_id, role = current_user_data

    await service.soft_delete_location(
        user_id=user_id,
        role=role,
        location_id=location_id,
    )


@router.put(
    "/{location_id}/company",
    response_model=LocationResponse,
)
async def assign_company_to_location(
    location_id: int,
    payload: LocationAssignCompanyRequest,
    service: LocationService = Depends(get_location_service),
    current_user_data: tuple[int, UserRole] = Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
                UserRole.ADMIN,
            ],
        ),
    ),
) -> LocationResponse:
    """Assign a company to a location."""
    user_id, role = current_user_data

    location = await service.assign_company_to_location(
        user_id=user_id,
        role=role,
        location_id=location_id,
        payload=payload,
    )
    return location


@router.post(
    "/{location_id}/users",
    response_model=LocationUserAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def assign_user_to_location(
    location_id: int,
    payload: LocationAssignUserRequest,
    service: LocationService = Depends(get_location_service),
    current_user_data: tuple[int, UserRole] = Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
                UserRole.ADMIN,
                UserRole.SUBADMIN,
            ],
        ),
    ),
) -> LocationUserAssignmentResponse:
    """Assign a user (janitor/portero) to a location."""
    user_id, role = current_user_data

    link = await service.assign_user_to_location(
        requester_id=user_id,
        requester_role=role,
        location_id=location_id,
        payload=payload,
    )
    return link
