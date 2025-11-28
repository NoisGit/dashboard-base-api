from __future__ import annotations

"""
Users router for Sentinel Enterprise API.

This module provides the initial read-only endpoints for the Users module:

- GET /api/users           -> paginated list of active users with basic filters
- GET /api/users/{user_id} -> user detail

Security:
- All endpoints require a valid access token (get_current_user).
- For now, only ADMIN and SUPERADMIN can list all users.
- Other roles can only view their own user detail (self).

Write operations (POST/PUT/DELETE) and full RBAC enforcement
will be implemented in a follow-up step.
"""

from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel, Field, select

from src.database import get_session
from src.auth.utils import get_current_user
from src.models import User, CompanyStaff

router = APIRouter(
    prefix="/api",
    tags=["users"],
)

# -------------------------------------------------------------------
# Roles (string values as they appear in the JWT payload)
# -------------------------------------------------------------------

ROLE_SUPERADMIN = "superadmin"
ROLE_ADMIN = "admin"
ROLE_SUBADMIN = "subadmin"
ROLE_JANITOR = "janitor"
ROLE_CLIENT = "client"


# -------------------------------------------------------------------
# Pydantic / SQLModel schemas for API I/O
# -------------------------------------------------------------------


class UserBase(SQLModel):
    """Base fields returned for a user in API responses."""
    username: str = Field(max_length=50)
    full_name: str = Field(max_length=100)
    email: str = Field(max_length=100)
    role: str = Field(max_length=10)
    status: bool
    is_active: bool


class UserRead(UserBase):
    """User representation used in list/detail responses."""
    id: int
    plan_id: int
    created_at: Optional[str] = None  # serialized datetime

    class Config:
        from_attributes = True


# -------------------------------------------------------------------
# Auth / helper utilities
# -------------------------------------------------------------------


def _get_role(current_user: Dict[str, Any]) -> str:
    role = current_user.get("role")
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Role not found in token payload.",
        )
    return role


def _get_user_id(current_user: Dict[str, Any]) -> int:
    user_id = current_user.get("user_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="user_id not found in token payload.",
        )
    return int(user_id)


def ensure_authenticated(current_user: Dict[str, Any]) -> None:
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )


def ensure_can_list_users(current_user: Dict[str, Any]) -> None:
    """
    For the initial version, only ADMIN and SUPERADMIN
    are allowed to list all users.
    """
    role = _get_role(current_user)
    if role not in {ROLE_ADMIN, ROLE_SUPERADMIN}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to list users.",
        )


# -------------------------------------------------------------------
# Endpoints
# -------------------------------------------------------------------


@router.get("/users", response_model=List[UserRead])
async def list_users(
    role: Optional[str] = None,
    company_id: Optional[int] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    session: AsyncSession = Depends(get_session),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> List[UserRead]:
    """
    Paginated list of active users.

    For now:
    - Only ADMIN and SUPERADMIN can access this endpoint.
    - Results include only users where is_active = True.
    - Optional filters:
      * role: filter by user role (admin, janitor, subadmin, client, etc.)
      * company_id: filter users linked to a given company via company_staff
      * search: partial match on full_name or username
    """
    ensure_authenticated(current_user)
    ensure_can_list_users(current_user)

    # Base query: only active users
    stmt = select(User).where(User.is_active == True)  # noqa: E712

    # Filter by role, if provided
    if role:
        stmt = stmt.where(User.role == role)

    # Filter by search (full_name or username)
    if search:
        like_pattern = f"%{search}%"
        stmt = stmt.where(
            (User.full_name.ilike(like_pattern))  # type: ignore[attr-defined]
            | (User.username.ilike(like_pattern))  # type: ignore[attr-defined]
        )

    # Filter by company via company_staff join
    if company_id is not None:
        stmt = (
            stmt.join(CompanyStaff, CompanyStaff.user_id == User.id)
            .where(CompanyStaff.company_id == company_id)
        )

    # Simple pagination (page 1-based)
    if page < 1:
        page = 1
    if page_size <= 0:
        page_size = 20

    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)

    result = await session.execute(stmt)
    users = result.scalars().all()
    return users


@router.get("/users/{user_id}", response_model=UserRead)
async def get_user_detail(
    user_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> UserRead:
    """
    Retrieve a single active user by ID.

    Access rules for this initial version:
    - SUPERADMIN and ADMIN can view any active user.
    - Other roles can only view their own user (self).
    """
    ensure_authenticated(current_user)
    requester_role = _get_role(current_user)
    requester_id = _get_user_id(current_user)

    user = await session.get(User, user_id)

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    # If not ADMIN / SUPERADMIN, only allow access to own record
    if requester_role not in {ROLE_ADMIN, ROLE_SUPERADMIN} and requester_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to view this user.",
        )

    return user
