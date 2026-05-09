"""Emergency contacts router module for Coredeck API."""

from fastapi_pagination import Page, Params
from fastapi import APIRouter, Depends, status

from src.auth.utils import get_current_user
from src.auth.permissions import RoleChecker
from src.core.enums import UserRole
from src.dependencies import get_emergency_contact_service
from src.schemas import (
    EmptyResponse,
    EmergencyContactCreateRequest,
    EmergencyContactUpdateRequest,
    EmergencyContactResponse,
)
from src.services.emergency_contact_service import EmergencyContactService

router = APIRouter(prefix="/emergency-contacts", tags=["emergency-contacts"])


@router.get(
    "/",
    response_model=Page[EmergencyContactResponse],
)
async def list_emergency_contacts(
    location_id: int,
    params: Params = Depends(),
    service: EmergencyContactService = Depends(get_emergency_contact_service),
    _=Depends(get_current_user),
):
    """
    List emergency contacts for a location.
    """
    emergency_contacts = await service.list_emergency_contacts(location_id, params)
    return emergency_contacts


@router.get(
    "/{contact_id}",
    response_model=EmergencyContactResponse,
)
async def get_emergency_contact_detail(
    contact_id: int,
    service: EmergencyContactService = Depends(get_emergency_contact_service),
    _=Depends(get_current_user),
):
    """
    Get a single emergency contact by ID.
    """
    contact = await service.get_emergency_contact_detail(contact_id=contact_id)
    return contact


@router.post(
    "/",
    response_model=EmptyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_emergency_contact(
    payload: EmergencyContactCreateRequest,
    service: EmergencyContactService = Depends(get_emergency_contact_service),
    user_id=Depends(RoleChecker([
        UserRole.SUPERADMIN,
        UserRole.ADMIN,
        UserRole.SUBADMIN,
    ])),
):
    """
    Create a new emergency contact.
    """

    await service.create_emergency_contact(user_id, payload)
    return EmptyResponse()


@router.put(
    "/{contact_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def update_emergency_contact(
    contact_id: int,
    payload: EmergencyContactUpdateRequest,
    service: EmergencyContactService = Depends(get_emergency_contact_service),
    user_id=Depends(RoleChecker([
        UserRole.SUPERADMIN,
        UserRole.ADMIN,
        UserRole.SUBADMIN,
    ])),
):
    """
    Update an existing emergency contact.
    """
    await service.update_emergency_contact(user_id, contact_id, payload)


@router.delete(
    "/{contact_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_emergency_contact(
    contact_id: int,
    service: EmergencyContactService = Depends(get_emergency_contact_service),
    user_id=Depends(RoleChecker([
        UserRole.SUPERADMIN,
        UserRole.ADMIN,
        UserRole.SUBADMIN,
    ])),
):
    """
    Delete an emergency contact.
    """
    await service.delete_emergency_contact(user_id, contact_id)
