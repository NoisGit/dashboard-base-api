"""Whitelists router module for Sentinel Enterprise API."""

from typing import Optional

from fastapi import APIRouter, Depends, status
from fastapi_pagination import Page, Params

from src.auth.permissions import RoleChecker
from src.core.enums import UserRole
from src.dependencies import get_whitelist_service
from src.schemas import (
    WhitelistCheckRequest,
    WhitelistCheckResponse,
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
    params: Params = Depends(),
    location_id: Optional[int] = None,
    company_id: Optional[int] = None,
    search: Optional[str] = None,
    include_expired: bool = False,
    service: WhitelistService = Depends(get_whitelist_service),
    user_id: int = Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
                UserRole.ADMIN,
                UserRole.SUBADMIN,
                UserRole.CLIENT,
            ],
        )
    ),
) -> Page[WhitelistResponse]:
    """List whitelist entries for a location."""
    return await service.list_whitelist(
        user_id=user_id,
        location_id=location_id,
        company_id=company_id,
        params=params,
        search=search,
        include_expired=include_expired,
    )


@router.post(
    "/",
    response_model=WhitelistResponse,
    status_code=status.HTTP_201_CREATED,
)
async def allow_person(
    payload: WhitelistCreateRequest,
    location_id: Optional[int] = None,
    company_id: Optional[int] = None,
    service: WhitelistService = Depends(get_whitelist_service),
    user_id: int = Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
                UserRole.ADMIN,
                UserRole.SUBADMIN,
                UserRole.CLIENT,
            ],
        )
    ),
) -> WhitelistResponse:
    """Allow a person for a location."""
    return await service.allow_person(
        user_id=user_id,
        location_id=location_id,
        company_id=company_id,
        payload=payload,
    )


@router.delete(
    "/{id_number}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def revoke_person(
    id_number: str,
    location_id: Optional[int] = None,
    company_id: Optional[int] = None,
    service: WhitelistService = Depends(get_whitelist_service),
    user_id: int = Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
                UserRole.ADMIN,
                UserRole.SUBADMIN,
                UserRole.CLIENT,
            ],
        )
    ),
):
    """Revoke a person whitelist access for a location."""
    await service.revoke_person(
        user_id=user_id,
        location_id=location_id,
        company_id=company_id,
        id_number=id_number,
    )


@router.post(
    "/check",
    response_model=WhitelistCheckResponse,
    status_code=status.HTTP_200_OK,
)
async def check_whitelist(
    location_id: int,
    payload: WhitelistCheckRequest,
    service: WhitelistService = Depends(get_whitelist_service),
    user_id: int = Depends(RoleChecker([UserRole.JANITOR])),
) -> WhitelistCheckResponse:
    """Check if a person is in whitelist (no AccessLog)."""
    return await service.check_whitelist(
        user_id=user_id,
        location_id=location_id,
        id_number=payload.id_number,
    )
