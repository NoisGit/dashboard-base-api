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
    """List active locations (porterías) visible for the current user."""
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
    """Get a single active location by ID."""
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
    """Create a new location (portería)."""
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
    """Update an existing location."""
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
    """Soft delete a location (is_active = False)."""
    await service.soft_delete_location(
        current_user=current_user,
        location_id=location_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put(
    "/{location_id}/company",
    response_model=LocationResponse,
)
async def assign_company_to_location(
    location_id: int,
    payload: LocationAssignCompanyRequest,
    service: LocationService = Depends(get_location_service),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> LocationResponse:
    """Assign a company to a location."""
    location = await service.assign_company_to_location(
        current_user=current_user,
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
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> LocationUserAssignmentResponse:
    """Assign a user (janitor/portero) to a location."""
    link = await service.assign_user_to_location(
        current_user=current_user,
        location_id=location_id,
        payload=payload,
    )
    return link
