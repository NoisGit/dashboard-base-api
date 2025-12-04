"""Locations router module for Sentinel Enterprise API."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query, Response, status

from src.auth.utils import get_current_user
from src.dependencies import get_location_service
from src.schemas import (
    LocationCreateRequest,
    LocationUpdateRequest,
    LocationResponse,
)
from src.services.location_service import LocationService

router = APIRouter(
    prefix="/locations",
    tags=["locations"],
)


@router.get(
    "/",
    response_model=List[LocationResponse],
)
async def list_locations(
    company_id: Optional[int] = Query(default=None),
    search: Optional[str] = Query(default=None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: LocationService = Depends(get_location_service),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> List[LocationResponse]:
    """
    List active locations (porterías) visible for the current user.

    RBAC rules are implemented inside LocationService.
    """
    locations = await service.list_locations(
        current_user=current_user,
        company_id=company_id,
        search=search,
        page=page,
        page_size=page_size,
    )
    return locations


@router.get(
    "/{location_id}",
    response_model=LocationResponse,
)
async def get_location_detail(
    location_id: int,
    service: LocationService = Depends(get_location_service),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> LocationResponse:
    """
    Get a single active location by ID.

    RBAC rules are implemented inside LocationService.
    """
    location = await service.get_location_detail(
        current_user=current_user,
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
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> LocationResponse:
    """
    Create a new location (portería).

    Only SUPERADMIN/ADMIN can create locations (enforced in LocationService).
    """
    location = await service.create_location(
        current_user=current_user,
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
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> LocationResponse:
    """
    Update an existing location.

    RBAC for who can update is enforced in LocationService.
    """
    location = await service.update_location(
        current_user=current_user,
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
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Response:
    """
    Soft delete a location (is_active = False).

    RBAC for who can delete is enforced in LocationService.
    """
    await service.soft_delete_location(
        current_user=current_user,
        location_id=location_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
