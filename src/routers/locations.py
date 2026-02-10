"""Locations router module for Sentinel Enterprise API."""

from typing import Optional

from fastapi import APIRouter, Depends, status
from fastapi_pagination import Page, Params

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
    params: Params = Depends(),
    company_id: Optional[int] = None,
    search: Optional[str] = None,
    service: LocationService = Depends(get_location_service),
    user_id: int = Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
                UserRole.ADMIN,
                UserRole.SUBADMIN,
                UserRole.CLIENT,
            ],
        ),
    ),
) -> Page[LocationResponse]:
    """List active locations (porterías) visible for the current user."""
    locations = await service.list_locations(
        user_id=user_id,
        params=params,
        company_id=company_id,
        search=search,
    )
    return locations


@router.get(
    "/{location_id}",
    response_model=LocationResponse,
)
async def get_location_detail(
    location_id: int,
    service: LocationService = Depends(get_location_service),
    user_id: int = Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
                UserRole.ADMIN,
                UserRole.SUBADMIN,
                UserRole.CLIENT,
                UserRole.JANITOR,
            ],
        ),
    ),
) -> LocationResponse:
    """Get a single active location by ID."""
    location = await service.get_location_detail(
        user_id=user_id,
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
    user_id=Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
                UserRole.ADMIN,
            ],
        ),
    ),
) -> LocationResponse:
    """Create a new location (portería)."""
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
    _=Depends(
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
    location = await service.update_location(
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
    _=Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
                UserRole.ADMIN,
            ],
        ),
    ),
):
    """Soft delete a location (is_active = False)."""
    await service.soft_delete_location(
        location_id=location_id,
    )


@router.post(
    "/{location_id}/company",
    response_model=LocationResponse,
)
async def assign_company_to_location(
    location_id: int,
    payload: LocationAssignCompanyRequest,
    service: LocationService = Depends(get_location_service),
    requester_id: int = Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
                UserRole.ADMIN,
            ],
        ),
    ),
) -> LocationResponse:
    """Assign a company to a location."""
    location = await service.assign_company_to_location(
        requester_id=requester_id,
        location_id=location_id,
        payload=payload,
    )
    return location


@router.post(
    "/{location_id}/users",
    status_code=status.HTTP_201_CREATED,
)
async def assign_user_to_location(
    location_id: int,
    payload: LocationAssignUserRequest,
    service: LocationService = Depends(get_location_service),
    requester_id=Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
                UserRole.ADMIN,
                UserRole.SUBADMIN,
            ],
        ),
    ),
):
    """Assign a user (janitor/portero) to a location."""
    await service.assign_user_to_location(
        requester_id=requester_id,
        location_id=location_id,
        payload=payload,
    )
