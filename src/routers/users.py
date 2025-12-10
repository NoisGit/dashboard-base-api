"""User router module for Sentinel Enterprise API."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query, status, HTTPException
from fastapi_pagination import Page, Params

from src.auth.utils import get_user_data_from_token
from src.core.enums import UserRole
from src.dependencies import get_user_service
from src.schemas import UserCreateRequest, UserUpdateRequest, UserResponse
from src.services.user_service import UserService

router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@router.get(
    "/",
    response_model=Page[UserResponse],
)
async def list_users(
    params: Params = Depends(),
    role: Optional[UserRole] = Query(default=None),
    company_id: Optional[int] = Query(default=None),
    search: Optional[str] = Query(default=None),
    service: UserService = Depends(get_user_service),
    current_user_data: tuple[int, UserRole] = Depends(
        get_user_data_from_token),
) -> Page[UserResponse]:
    """List active users with filters and pagination."""
    _, requester_role = current_user_data

    if requester_role not in {UserRole.SUPERADMIN, UserRole.ADMIN}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to list users.",
        )

    return await service.list_users(
        role=role,
        company_id=company_id,
        search=search,
        params=params,
    )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
)
async def get_user_detail(
    user_id: int,
    service: UserService = Depends(get_user_service),
    current_user_data: tuple[int, UserRole] = Depends(
        get_user_data_from_token),
) -> UserResponse:
    """Get a single active user by ID."""
    requester_id, requester_role = current_user_data

    user = await service.get_user_detail(
        requester_id=requester_id,
        requester_role=requester_role,
        user_id=user_id,
    )
    return user


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    payload: UserCreateRequest,
    service: UserService = Depends(get_user_service),
    current_user_data: tuple[int, UserRole] = Depends(
        get_user_data_from_token),
) -> UserResponse:
    """Create a new user (email unique, password hashed with Argon2)."""
    requester_id, requester_role = current_user_data

    if requester_role not in {UserRole.SUPERADMIN, UserRole.ADMIN}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to create users.",
        )

    user = await service.create_user(
        requester_id=requester_id,
        requester_role=requester_role,
        payload=payload,
    )
    return user


@router.put(
    "/{user_id}",
    response_model=UserResponse,
)
async def update_user(
    user_id: int,
    payload: UserUpdateRequest,
    service: UserService = Depends(get_user_service),
    current_user_data: tuple[int, UserRole] = Depends(
        get_user_data_from_token),
) -> UserResponse:
    """Update user profile (name, email, role, status)."""
    requester_id, requester_role = current_user_data

    user = await service.update_user(
        requester_id=requester_id,
        requester_role=requester_role,
        user_id=user_id,
        payload=payload,
    )
    return user


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
    current_user_data: tuple[int, UserRole] = Depends(
        get_user_data_from_token),
):
    """Soft delete user by setting is_active = False."""
    _, requester_role = current_user_data

    if requester_role is not UserRole.SUPERADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to delete users.",
        )

    await service.soft_delete_user(
        requester_role=requester_role,
        user_id=user_id,
    )
