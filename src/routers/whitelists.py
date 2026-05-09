"""Whitelists router module for Coredeck API."""

from typing import Optional

from fastapi import APIRouter, Depends, File, UploadFile, status
from fastapi_pagination import Page, Params

from src.auth.permissions import RoleChecker
from src.core.enums import UserRole
from src.dependencies import get_whitelist_service
from src.schemas import (
    EmptyResponse,
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


@router.post(
    "/bulk",
    response_model=EmptyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def bulk_import_whitelist(
    location_id: int,
    file: UploadFile = File(...),
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
) -> EmptyResponse:
    """Allow a person for a location."""
    await service.bulk_import_whitelist(
        user_id=user_id,
        location_id=location_id,
        file=file,
    )
    return EmptyResponse()


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
