"""Blacklists router module for Sentinel Enterprise API."""

from typing import Optional

from fastapi import APIRouter, Depends, status
from fastapi_pagination import Page, Params

from src.auth.permissions import RoleChecker
from src.core.enums import UserRole
from src.dependencies import get_blacklist_service
from src.schemas import (
    BlacklistCheckRequest,
    BlacklistCheckResponse,
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
    params: Params = Depends(),
    location_id: Optional[int] = None,
    company_id: Optional[int] = None,
    search: Optional[str] = None,
    service: BlacklistService = Depends(get_blacklist_service),
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
) -> Page[BlacklistResponse]:
    """List blacklist entries."""
    return await service.list_blacklist(
        user_id=user_id,
        location_id=location_id,
        company_id=company_id,
        params=params,
        search=search,
    )


@router.post(
    "/",
    response_model=BlacklistResponse,
    status_code=status.HTTP_201_CREATED,
)
async def block_person(
    payload: BlacklistCreateRequest,
    location_id: Optional[int] = None,
    company_id: Optional[int] = None,
    service: BlacklistService = Depends(get_blacklist_service),
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
) -> BlacklistResponse:
    """Block a person for a location."""
    return await service.block_person(
        user_id=user_id,
        location_id=location_id,
        company_id=company_id,
        payload=payload,
    )


@router.delete(
    "/{id_number}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def unblock_person(
    id_number: str,
    location_id: Optional[int] = None,
    company_id: Optional[int] = None,
    service: BlacklistService = Depends(get_blacklist_service),
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
) -> None:
    """Unblock a person for a location."""
    await service.unblock_person(
        user_id=user_id,
        location_id=location_id,
        company_id=company_id,
        id_number=id_number,
    )


@router.post(
    "/check",
    response_model=BlacklistCheckResponse,
    status_code=status.HTTP_200_OK,
)
async def check_blacklist(
    location_id: int,
    payload: BlacklistCheckRequest,
    service: BlacklistService = Depends(get_blacklist_service),
    user_id: int = Depends(RoleChecker([UserRole.JANITOR])),
) -> BlacklistCheckResponse:
    """Check if a person is in blacklist (no AccessLog)."""
    return await service.check_blacklist(
        user_id=user_id,
        location_id=location_id,
        id_number=payload.id_number,
    )
