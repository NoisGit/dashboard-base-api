"""Service contacts router module for Sentinel Enterprise API."""

from fastapi_pagination import Page, Params
from fastapi import APIRouter, Depends, status

from src.auth.utils import get_current_user
from src.auth.permissions import RoleChecker
from src.core.enums import UserRole
from src.dependencies import get_service_contact_service
from src.schemas import (
    EmptyResponse,
    ServiceContactResponse,
    ServiceContactCreateRequest
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
    _=Depends(get_current_user),
):
    """
    List service contacts for a location.
    """
    service_contacts = await service.list_service_contacts(location_id, params)
    return service_contacts


@router.post(
    "/",
    response_model=EmptyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_service_contact(
    payload: ServiceContactCreateRequest,
    service: ServiceContactService = Depends(get_service_contact_service),
    user_id=Depends(RoleChecker([
        UserRole.SUPERADMIN,
        UserRole.ADMIN,
        UserRole.SUBADMIN,
    ])),
):
    """
    Create a new service contact.
    """

    await service.create_service_contact(user_id, payload)
    return EmptyResponse()
