"""Service contacts router module for Locentr API."""

from fastapi_pagination import Page, Params
from fastapi import APIRouter, Depends, File, UploadFile, status

from src.auth.permissions import RoleChecker
from src.core.enums import UserRole
from src.dependencies import get_service_contact_service
from src.schemas import (
    EmptyResponse,
    ServiceContactResponse,
    ServiceContactCreateRequest,
    ServiceContactUpdateRequest,
)
from src.services.service_contact_service import ServiceContactService

router = APIRouter(prefix="/service-contacts", tags=["service-contacts"])


@router.get(
    "/",
    response_model=Page[ServiceContactResponse],
)
async def list_service_contacts(
    location_id: int,
    params: Params = Depends(),
    service: ServiceContactService = Depends(get_service_contact_service),
    user_id: int = Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
                UserRole.ADMIN,
                UserRole.CLIENT,
            ],
        )
    ),
):
    """
    List service contacts for a location.
    """
    service_contacts = await service.list_service_contacts(location_id, user_id, params)
    return service_contacts


@router.post(
    "/",
    response_model=EmptyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_service_contact(
    payload: ServiceContactCreateRequest,
    service: ServiceContactService = Depends(get_service_contact_service),
    user_id: int = Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
                UserRole.ADMIN,
                UserRole.CLIENT,
            ],
        )
    ),
):
    """
    Create a new service contact.
    """

    await service.create_service_contact(user_id, payload)
    return EmptyResponse()


@router.post(
    "/{location_id}/bulk",
    response_model=EmptyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def bulk_import_service_contacts(
    location_id: int,
    file: UploadFile = File(...),
    service: ServiceContactService = Depends(get_service_contact_service),
    user_id: int = Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
                UserRole.ADMIN,
            ],
        )
    ),
):
    """
    Create a new service contact.
    """

    await service.bulk_import_service_contacts(
        user_id=user_id,
        location_id=location_id,
        file=file,
    )
    return EmptyResponse()


@router.put(
    "/{contact_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def update_service_contact(
    contact_id: int,
    payload: ServiceContactUpdateRequest,
    service: ServiceContactService = Depends(get_service_contact_service),
    user_id: int = Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
                UserRole.ADMIN,
                UserRole.CLIENT,
            ],
        )
    ),
):
    """
    Update an existing service contact.
    """
    await service.update_service_contact(user_id, contact_id, payload)


@router.delete(
    "/{contact_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_service_contact(
    contact_id: int,
    service: ServiceContactService = Depends(get_service_contact_service),
    user_id: int = Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
                UserRole.ADMIN,
                UserRole.CLIENT,
            ],
        )
    ),
) -> None:
    """
    Delete an service contact.
    """
    await service.delete_service_contact(user_id, contact_id)
