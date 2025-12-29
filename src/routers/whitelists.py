"""Whitelists router module for Sentinel Enterprise API."""

from typing import Optional

from fastapi import APIRouter, Depends, status
from fastapi_pagination import Page, Params

from src.auth.permissions import RoleChecker
from src.core.enums import UserRole
from src.dependencies import get_whitelist_service
from src.schemas import (
    WhitelistCreateRequest,
    WhitelistResponse,
)
from src.services.whitelist_service import WhitelistService

router = APIRouter(prefix="/whitelists", tags=["whitelists"])


@router.get(
    "/",
    response_model=Page[WhitelistResponse],
)
async def list_whitelist(
    location_id: int,
    params: Params = Depends(),
    search: Optional[str] = None,
    include_expired: bool = False,
    service: WhitelistService = Depends(get_whitelist_service),
    user_id: int = Depends(RoleChecker([
        UserRole.SUPERADMIN,
        UserRole.ADMIN,
        UserRole.SUBADMIN,
    ])),
) -> Page[WhitelistResponse]:
    """List whitelist entries for a location."""
    whitelist = await service.list_whitelist(
        user_id=user_id,
        location_id=location_id,
        params=params,
        search=search,
        include_expired=include_expired,
    )
    return whitelist


@router.post(
    "/",
    response_model=WhitelistResponse,
    status_code=status.HTTP_201_CREATED,
)
async def allow_person(
    location_id: int,
    payload: WhitelistCreateRequest,
    service: WhitelistService = Depends(get_whitelist_service),
    user_id: int = Depends(RoleChecker([
        UserRole.SUPERADMIN,
        UserRole.ADMIN,
        UserRole.SUBADMIN,
    ])),
) -> WhitelistResponse:
    """Allow a person for a location."""
    entry = await service.allow_person(
        user_id=user_id,
        location_id=location_id,
        payload=payload,
    )
    return entry


@router.delete(
    "/{id_number}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def revoke_person(
    id_number: str,
    location_id: int,
    service: WhitelistService = Depends(get_whitelist_service),
    user_id: int = Depends(RoleChecker([
        UserRole.SUPERADMIN,
        UserRole.ADMIN,
        UserRole.SUBADMIN,
    ])),
):
    """Revoke a person whitelist access for a location."""
    await service.revoke_person(
        user_id=user_id,
        location_id=location_id,
        id_number=id_number,
    )
