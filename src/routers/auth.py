"""Auth router module for Sentinel Enterprise API."""

from fastapi import APIRouter, Depends, status

from src.auth import get_current_user
from src.auth.utils import get_user_id_from_token
from src.dependencies import get_auth_service
from src.schemas import (
    UserLoginRequest,
    UserTokenResponse,
    RefreshTokenRequest,
    AccessTokenResponse,
)
from src.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=UserTokenResponse)
async def login_user(
    user_data: UserLoginRequest,
    service: AuthService = Depends(get_auth_service)
):
    """User login endpoint"""
    user_token = await service.login_user(user_data)
    return user_token


@router.post("/refresh", response_model=UserTokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    service: AuthService = Depends(get_auth_service),
    _=Depends(get_current_user)
):
    """Refresh access token using a valid refresh token"""
    user_token = await service.refresh_token(refresh_data)
    return user_token


@router.post("/refresh-access-token", response_model=AccessTokenResponse)
async def refresh_access_token_only(
    refresh_data: RefreshTokenRequest,
    service: AuthService = Depends(get_auth_service),
    _=Depends(get_current_user)
):
    """Refresh access token only using a valid refresh token"""
    user_access_token = await service.refresh_access_token_only(refresh_data)
    return user_access_token


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout_user(
    service: AuthService = Depends(get_auth_service),
    user_id=Depends(get_user_id_from_token)
):
    """Logout user by clearing refresh token"""
    await service.logout_user(user_id)
