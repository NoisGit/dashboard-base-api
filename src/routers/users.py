"""User router module for Sentinel Enterprise API."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Response, status

from src.auth.utils import get_current_user
from src.dependencies import get_user_service
from src.schemas import UserCreateRequest, UserUpdateRequest, UserResponse
from src.services.user_service import UserService

router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@router.get("/", response_model=List[UserResponse])
async def list_users(
    role: Optional[str] = None,
    company_id: Optional[int] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    service: UserService = Depends(get_user_service),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> List[UserResponse]:
    """List active users with pagination and filters."""
    users = await service.list_users(
        current_user=current_user,
        role=role,
        company_id=company_id,
        search=search,
        page=page,
        page_size=page_size,
    )
    return users


@router.get("/{user_id}", response_model=UserResponse)
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
) -> UserResponse:
    """Create a new user (email unique, password hashed with Argon2)."""
    user = await service.create_user(
        current_user=current_user,
        payload=payload,
    )
    return user


@router.put("/{user_id}", response_model=UserResponse)
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
) -> Response:
    """Soft delete user by setting is_active to False."""
    await service.soft_delete_user(
        current_user=current_user,
        user_id=user_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
