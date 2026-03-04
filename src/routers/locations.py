"""Locations router module for Sentinel Enterprise API."""

from typing import Optional, List

from fastapi import APIRouter, Depends, status
from fastapi_pagination import Page, Params

from src.auth.permissions import RoleChecker
from src.core.enums import UserRole
from src.dependencies import get_location_service
from src.schemas import (
    EmptyResponse,
    LocationCreateRequest,
    LocationUpdateRequest,
    LocationResponse,
    LocationAssignCompanyRequest,
    LocationAssignUserRequest,
    AccessListResponse,
    UserResponse,
)
from src.schemas.location_custom_form_schemas import (
    LocationCustomFormResponse,
    LocationCustomFormUpsertRequest,
    LocationCustomFieldUpdateRequest,
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
):
    """List active locations (porterías) visible for the current user."""
    return await service.list_locations(
        user_id=user_id,
        params=params,
        company_id=company_id,
        search=search,
    )


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
):
    """Get a single active location by ID."""
    return await service.get_location_detail(
        user_id=user_id,
        location_id=location_id,
    )


@router.post(
    "/",
    response_model=EmptyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_location(
    payload: LocationCreateRequest,
    service: LocationService = Depends(get_location_service),
    user_id: int = Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
                UserRole.ADMIN,
            ],
        ),
    ),
):
    """Create a new location (portería)."""
    await service.create_location(
        user_id=user_id,
        payload=payload,
    )
    return EmptyResponse()


@router.put(
    "/{location_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def update_location(
    location_id: int,
    payload: LocationUpdateRequest,
    service: LocationService = Depends(get_location_service),
    _: int = Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
                UserRole.ADMIN,
                UserRole.SUBADMIN,
            ],
        ),
    ),
):
    """Update an existing location."""
    await service.update_location(
        location_id=location_id,
        payload=payload,
    )


@router.delete(
    "/{location_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_location(
    location_id: int,
    service: LocationService = Depends(get_location_service),
    _: int = Depends(
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
    response_model=EmptyResponse,
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
):
    """Assign a company to a location."""
    await service.assign_company_to_location(
        requester_id=requester_id,
        location_id=location_id,
        payload=payload,
    )
    return EmptyResponse()


@router.post(
    "/{location_id}/users",
    response_model=EmptyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def assign_user_to_location(
    location_id: int,
    payload: LocationAssignUserRequest,
    service: LocationService = Depends(get_location_service),
    requester_id: int = Depends(
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
    return EmptyResponse()


@router.get(
    "/{location_id}/custom-form",
    response_model=LocationCustomFormResponse,
)
async def get_location_custom_form(
    location_id: int,
    service: LocationService = Depends(get_location_service),
    user_id: int = Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
                UserRole.ADMIN,
                UserRole.SUBADMIN,
            ],
        ),
    ),
):
    """Get custom fields for a location."""
    return await service.get_location_custom_form(
        user_id=user_id,
        location_id=location_id,
    )


@router.post(
    "/{location_id}/custom-form/fields",
    response_model=EmptyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_location_custom_form_fields(
    location_id: int,
    payload: LocationCustomFormUpsertRequest,
    service: LocationService = Depends(get_location_service),
    user_id: int = Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
                UserRole.ADMIN,
                UserRole.SUBADMIN,
            ],
        ),
    ),
):
    """Create custom form fields for a location."""
    await service.create_location_custom_form_fields(
        user_id=user_id,
        location_id=location_id,
        payload=payload,
    )
    return EmptyResponse()


@router.put(
    "/{location_id}/custom-form/fields/{custom_form_field_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def update_location_custom_form_field(
    location_id: int,
    custom_form_field_id: int,
    payload: LocationCustomFieldUpdateRequest,
    service: LocationService = Depends(get_location_service),
    user_id: int = Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
                UserRole.ADMIN,
                UserRole.SUBADMIN,
            ],
        ),
    ),
):
    """Update a custom form field for a location."""
    await service.update_location_custom_form_field(
        user_id=user_id,
        location_id=location_id,
        custom_form_field_id=custom_form_field_id,
        payload=payload,
    )


@router.get(
    "/{location_id}/access_lists",
    response_model=List[AccessListResponse],
)
async def get_location_access_lists(
    location_id: int,
    service: LocationService = Depends(get_location_service),
    user_id: int = Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
                UserRole.JANITOR,
            ],
        ),
    ),
):
    """Get Access List for a location."""
    return await service.get_location_access_lists(
        user_id=user_id,
        location_id=location_id,
    )


@router.get(
    "/{location_id}/janitors",
    response_model=Page[UserResponse],
)
async def list_janitors(
    params: Params = Depends(),
    location_id: int = None,
    search: Optional[str] = None,
    service: LocationService = Depends(get_location_service),
    user_id: int = Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
                UserRole.ADMIN,
            ],
        ),
    ),
) -> Page[UserResponse]:
    """List active users with filters and pagination."""
    users = await service.list_janitors(
        user_id=user_id,
        location_id=location_id,
        search=search,
        params=params,
    )
    return users
