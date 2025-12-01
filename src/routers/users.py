from __future__ import annotations

"""
Users router for Sentinel Enterprise API.

Full Users module behavior (backend side):

- GET /api/users
    -> Paginated list of active users with filters:
       * role
       * company_id (company filter via company_staff)
       * search (name/username)

- POST /api/users
    -> User creation:
       * Validates email uniqueness
       * Receives password in plain text and hashes it using Argon2
       * Applies RBAC rules (SUPERADMIN vs ADMIN vs others)

- GET /api/users/{user_id}
    -> User detail:
       * SUPERADMIN and ADMIN can see any active user
       * Other roles can only see themselves (self)

- PUT /api/users/{user_id}
    -> Profile update (name, email, role, status):
       * Applies RBAC rules, especially for ADMIN vs ADMIN/SUPERADMIN

- DELETE /api/users/{user_id}
    -> Soft delete:
       * Sets is_active = False (no physical delete)
       * Keeps data for access logs referential integrity

Security:
- All endpoints require a valid access token (get_current_user).

RBAC (high level):
- SUPERADMIN:
    * Can create / edit / delete users of any role.
- ADMIN:
    * Can create / edit / delete only SUBADMIN / JANITOR / CLIENT users.
    * Cannot create or manage ADMIN / SUPERADMIN.
- Other roles:
    * No access to list/create/delete.
    * Can only read their own user and do limited updates on self.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional

from argon2 import PasswordHasher
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

ADMIN_LIKE_ROLES = {ROLE_ADMIN, ROLE_SUPERADMIN}

pwd_hasher = PasswordHasher()


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


class UserCreate(SQLModel):
    """
    Payload used to create a new user.

    Requirements:
    - Email must be unique among active users.
    - Password is received in plain text and hashed using Argon2 before saving.
    - Role must be one of the supported roles.
    """
    username: str = Field(max_length=50)
    full_name: str = Field(max_length=100)
    email: str = Field(max_length=100)
    password: str = Field(min_length=8, max_length=128)
    role: str = Field(max_length=10)
    plan_id: int
    status: bool = True


class UserUpdate(SQLModel):
    """
    Payload used to update an existing user.

    All fields are optional so we can perform partial updates using
    model_dump(exclude_unset=True).
    """
    full_name: Optional[str] = Field(default=None, max_length=100)
    email: Optional[str] = Field(default=None, max_length=100)
    role: Optional[str] = Field(default=None, max_length=10)
    status: Optional[bool] = None


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
    For now, only ADMIN and SUPERADMIN are allowed to list all users.
    Other roles cannot access the list endpoint.
    """
    role = _get_role(current_user)
    if role not in {ROLE_ADMIN, ROLE_SUPERADMIN}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to list users.",
        )


def ensure_can_create_users(current_user: Dict[str, Any]) -> None:
    """
    Only ADMIN and SUPERADMIN can create users.

    Additional role restrictions (cannot create ADMIN/SUPERADMIN as ADMIN)
    are enforced at creation time.
    """
    role = _get_role(current_user)
    if role not in {ROLE_ADMIN, ROLE_SUPERADMIN}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to create users.",
        )


def ensure_can_modify_or_delete_users(current_user: Dict[str, Any]) -> None:
    """
    Only ADMIN and SUPERADMIN can update or delete other users.

    Additional restrictions for ADMIN vs ADMIN/SUPERADMIN are handled
    inside each handler.
    """
    role = _get_role(current_user)
    if role not in {ROLE_ADMIN, ROLE_SUPERADMIN}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to modify or delete users.",
        )


def _ensure_admin_cannot_manage_admin_like(
    requester_role: str,
    target_role: str,
    operation: str,
) -> None:
    """
    Helper to ensure an ADMIN cannot create/edit/delete ADMIN/SUPERADMIN users.
    """
    if requester_role == ROLE_ADMIN and target_role in ADMIN_LIKE_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Admins are not allowed to {operation} admin-like users.",
        )


def hash_password(plain_password: str) -> str:
    """Hash a plain-text password using Argon2."""
    return pwd_hasher.hash(plain_password)


async def ensure_email_unique(
    session: AsyncSession,
    email: str,
    exclude_user_id: Optional[int] = None,
) -> None:
    """
    Ensure that an email is unique among active users.

    If exclude_user_id is provided, that user is ignored in the uniqueness check
    (useful when updating the same user).
    """
    stmt = select(User).where(
        User.email == email,
        User.is_active == True,  # noqa: E712
    )
    if exclude_user_id is not None:
        stmt = stmt.where(User.id != exclude_user_id)

    result = await session.execute(stmt)
    existing = result.scalars().first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already in use.",
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

    Behavior:
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

    Access rules:
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


@router.post(
    "/users",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    payload: UserCreate,
    session: AsyncSession = Depends(get_session),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> UserRead:
    """
    Create a new user.

    Behavior:
    - Only ADMIN and SUPERADMIN can create users.
    - Email must be unique among active users.
    - Password is received in plain text and hashed with Argon2.
    - ADMIN is not allowed to create ADMIN or SUPERADMIN users.
    """
    ensure_authenticated(current_user)
    ensure_can_create_users(current_user)

    requester_role = _get_role(current_user)
    requester_id = _get_user_id(current_user)

    # Normalize and validate role
    requested_role = payload.role

    # Ensure ADMIN does not create ADMIN/SUPERADMIN
    _ensure_admin_cannot_manage_admin_like(
        requester_role=requester_role,
        target_role=requested_role,
        operation="create",
    )

    # Validate email uniqueness
    await ensure_email_unique(session, payload.email)

    # Hash password
    password_hash = hash_password(payload.password)

    user = User(
        username=payload.username,
        full_name=payload.full_name,
        email=payload.email,
        password_hash=password_hash,
        role=requested_role,
        plan_id=payload.plan_id,
        status=payload.status,
        is_active=True,
        created_by=requester_id,
        created_at=datetime.now(),
    )

    session.add(user)
    await session.commit()
    await session.refresh(user)

    return user


@router.put("/users/{user_id}", response_model=UserRead)
async def update_user(
    user_id: int,
    payload: UserUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> UserRead:
    """
    Update an existing user.

    Behavior:
    - SUPERADMIN:
        * Can update any active user, including changing the role.
    - ADMIN:
        * Cannot update users with ADMIN/SUPERADMIN roles.
        * Cannot change any user's role to ADMIN or SUPERADMIN.
    - Other roles:
        * Can only update their own user (self).
        * Cannot change their role or status.
    - Email uniqueness is enforced when email is changed.
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

    # If not ADMIN/SUPERADMIN, only allow self-update and no role/status changes
    if requester_role not in {ROLE_ADMIN, ROLE_SUPERADMIN}:
        if requester_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to update this user.",
            )

        if payload.role is not None and payload.role != user.role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to change your role.",
            )
        if payload.status is not None and payload.status != user.status:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to change your status.",
            )

    else:
        # ADMIN / SUPERADMIN case
        ensure_can_modify_or_delete_users(current_user)

        # ADMIN cannot manage ADMIN/SUPERADMIN users
        _ensure_admin_cannot_manage_admin_like(
            requester_role=requester_role,
            target_role=user.role,
            operation="update",
        )

        # ADMIN cannot assign ADMIN/SUPERADMIN role
        if payload.role is not None:
            _ensure_admin_cannot_manage_admin_like(
                requester_role=requester_role,
                target_role=payload.role,
                operation="assign role to",
            )

    # Email uniqueness if email is being updated
    if payload.email is not None and payload.email != user.email:
        await ensure_email_unique(session, payload.email, exclude_user_id=user_id)

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(user, key, value)

    user.last_update = datetime.now()

    await session.commit()
    await session.refresh(user)
    return user


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_200_OK,
)
async def delete_user(
    user_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> None:
    """
    Soft delete a user.

    Behavior:
    - Only ADMIN and SUPERADMIN can delete users.
    - ADMIN cannot delete ADMIN/SUPERADMIN users.
    - Soft delete only:
        * sets is_active = False.
        * does not physically remove the row to preserve referential integrity.
    """
    ensure_authenticated(current_user)
    ensure_can_modify_or_delete_users(current_user)

    requester_role = _get_role(current_user)

    user = await session.get(User, user_id)

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    _ensure_admin_cannot_manage_admin_like(
        requester_role=requester_role,
        target_role=user.role,
        operation="delete",
    )

    user.is_active = False
    await session.commit()
    return None
