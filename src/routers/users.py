"""User router module for Sentinel Enterprise API."""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, status
from fastapi_pagination import Page, paginate

from src.auth.utils import get_current_user
from src.auth.permissions import RoleChecker
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
    role: Optional[str] = None,
    company_id: Optional[int] = None,
    search: Optional[str] = None,
    service: UserService = Depends(get_user_service),
    current_user: Dict[str, Any] = Depends(get_current_user),
    _: int = Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
                UserRole.ADMIN,
            ],
        ),
    ),
) -> Page[UserResponse]:
    """List active users with filters and pagination."""
    users = await service.list_users(
        current_user=current_user,
        role=role,
        company_id=company_id,
        search=search,
    )
    return paginate(users)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
)
async def get_user_detail(
    user_id: int,
    service: UserService = Depends(get_user_service),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> UserResponse:
    """Get a single active user by ID."""
    user = await service.get_user_detail(
        current_user=current_user,
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
    current_user: Dict[str, Any] = Depends(get_current_user),
    _: int = Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
                UserRole.ADMIN,
            ],
        ),
    ),
) -> UserResponse:
    """Create a new user (email unique, password hashed with Argon2)."""
    user = await service.create_user(
        current_user=current_user,
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
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> UserResponse:
    """Update user profile (name, email, role, status)."""
    user = await service.update_user(
        current_user=current_user,
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
    current_user: Dict[str, Any] = Depends(get_current_user),
    _: int = Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
                UserRole.ADMIN,
            ],
        ),
    ),
):
    """Soft delete user by setting is_active = False."""
    await service.soft_delete_user(
        current_user=current_user,
        user_id=user_id,
    )
    # 204 => no body
