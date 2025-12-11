"""User router module for Sentinel Enterprise API."""

from typing import Optional

from fastapi import APIRouter, Depends, status
from fastapi_pagination import Page, Params

from src.auth import get_current_user
from src.auth.utils import get_user_data_from_token, get_user_id_from_token
from src.auth.permissions import RoleChecker
from src.core.enums import UserRole
from src.dependencies import get_user_service
from src.schemas import (
    UserCreateRequest,
    UserUpdateRequest,
    UserResponse,
    UserLoginRequest,
    UserTokenResponse,
    RefreshTokenRequest,
    AccessTokenResponse)
from src.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/login", response_model=UserTokenResponse)
async def login_user(
    user_data: UserLoginRequest,
    service: UserService = Depends(get_user_service)
):
    """User login endpoint"""
    user_token = await service.login_user(user_data)
    return user_token


@router.post("/refresh", response_model=UserTokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    service: UserService = Depends(get_user_service),
    _=Depends(get_current_user)
):
    """Refresh access token using a valid refresh token"""
    user_token = await service.refresh_token(refresh_data)
    return user_token


@router.post("/refresh-access-token", response_model=AccessTokenResponse)
async def refresh_access_token_only(
    refresh_data: RefreshTokenRequest,
    service: UserService = Depends(get_user_service),
    _=Depends(get_current_user)
):
    """Refresh access token only using a valid refresh token"""
    user_access_token = await service.refresh_access_token_only(refresh_data)
    return user_access_token


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
    _=Depends(get_user_data_from_token),
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


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout_user(
    service: UserService = Depends(get_user_service),
    user_id=Depends(get_user_id_from_token)
):
    """Logout user by clearing FCM token"""
    await service.logout_user(user_id)
