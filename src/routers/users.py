"""User router module for Coredeck API."""

from typing import Optional

from fastapi import APIRouter, Depends, status
from fastapi_pagination import Page, Params

from src.auth.utils import get_user_id_from_token
from src.auth.permissions import RoleChecker
from src.core.enums import UserRole
from src.dependencies import get_user_service
from src.schemas import (
    UserCreateRequest,
    UserUpdateRequest,
    UserSuspendRequest,
    UserResponse,
    UserMeResponse,
    UserChangePasswordRequest,
)
from src.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserMeResponse)
async def get_current_user_profile(
    service: UserService = Depends(get_user_service),
    user_id: int = Depends(get_user_id_from_token),
) -> UserMeResponse:
    """Get current user profile."""
    user = await service.get_user_profile(user_id=user_id)
    return user


@router.get(
    "/",
    response_model=Page[UserResponse],
)
async def list_users(
    params: Params = Depends(),
    role: Optional[UserRole] = None,
    company_id: Optional[int] = None,
    search: Optional[str] = None,
    service: UserService = Depends(get_user_service),
    _=Depends(
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
        role=role,
        company_id=company_id,
        search=search,
        params=params,
    )
    return users


@router.get(
    "/{user_id}",
    response_model=UserResponse,
)
async def get_user_detail(
    user_id: int,
    service: UserService = Depends(get_user_service),
    _=Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
                UserRole.ADMIN,
            ],
        ),
    ),
) -> UserResponse:
    """Get user by ID."""
    user = await service.get_user_detail(
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
    _=Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
                UserRole.ADMIN,
            ],
        ),
    ),
) -> UserResponse:
    """Create a new user."""
    user = await service.create_user(
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
    _=Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
                UserRole.ADMIN,
            ],
        ),
    ),
) -> UserResponse:
    """Update user by ID."""
    user = await service.update_user(
        user_id=user_id,
        payload=payload,
    )
    return user


@router.patch(
    "/{user_id}/suspend",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def suspend_user(
    user_id: int,
    payload: UserSuspendRequest,
    service: UserService = Depends(get_user_service),
    _=Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
            ],
        ),
    ),
):
    """Suspend user."""
    await service.suspend_user(
        user_id=user_id,
        payload=payload,
    )


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
    _=Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
            ],
        ),
    ),
):
    """Soft delete user by setting is_active = False."""
    await service.soft_delete_user(
        user_id=user_id,
    )


@router.post(
    "/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def change_password(
    payload: UserChangePasswordRequest,
    service: UserService = Depends(get_user_service),
    user_id: int = Depends(get_user_id_from_token),
):
    """Change password for authenticated user."""
    await service.change_user_password(
        user_id=user_id,
        payload=payload,
    )
