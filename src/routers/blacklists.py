"""Blacklists router module for Sentinel Enterprise API."""

from typing import Optional

from fastapi import APIRouter, Depends, status
from fastapi_pagination import Page, Params

from src.auth.permissions import RoleChecker
from src.core.enums import UserRole
from src.dependencies import get_blacklist_service
from src.schemas import (
    BlacklistCreateRequest,
    BlacklistResponse,
)
from src.services.blacklist_service import BlacklistService

router = APIRouter(prefix="/blacklists", tags=["blacklists"])


@router.get(
    "/",
    response_model=Page[BlacklistResponse],
)
async def list_blacklist(
    location_id: int,
    params: Params = Depends(),
    search: Optional[str] = None,
    service: BlacklistService = Depends(get_blacklist_service),
    user_id: int = Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
                UserRole.ADMIN,
                UserRole.SUBADMIN,
            ],
        ),
    ),
) -> Page[BlacklistResponse]:
    """List blacklist entries for a location."""
    blacklist = await service.list_blacklist(
        user_id=user_id,
        location_id=location_id,
        params=params,
        search=search,
    )
    return blacklist


@router.post(
    "/",
    response_model=BlacklistResponse,
    status_code=status.HTTP_201_CREATED,
)
async def block_person(
    location_id: int,
    payload: BlacklistCreateRequest,
    service: BlacklistService = Depends(get_blacklist_service),
    user_id: int = Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
                UserRole.ADMIN,
                UserRole.SUBADMIN,
            ],
        ),
    ),
) -> BlacklistResponse:
    """Block a person for a location."""
    entry = await service.block_person(
        user_id=user_id,
        location_id=location_id,
        payload=payload,
    )
    return entry


@router.delete(
    "/{id_number}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def unblock_person(
    id_number: str,
    location_id: int,
    service: BlacklistService = Depends(get_blacklist_service),
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
    """Unblock a person for a location."""
    await service.unblock_person(
        user_id=user_id,
        location_id=location_id,
        id_number=id_number,
    )
