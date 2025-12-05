"""User service module for Sentinel Enterprise API."""

# pylint: disable=no-member, singleton-comparison

from datetime import datetime
from typing import Any, Dict, List, Optional, cast

from argon2 import PasswordHasher
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.core.enums import UserRole
from src.models import User, CompanyStaff
from src.schemas import UserCreateRequest, UserUpdateRequest

# Admin-like roles (string values from enum)
ADMIN_LIKE_ROLES = {
    UserRole.ADMIN.value,
    UserRole.SUPERADMIN.value,
}

pwd_hasher = PasswordHasher()


class UserService:
    """Service for user operations and business RBAC rules."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ---------- Current user helpers ----------

    def _get_role(self, current_user: Dict[str, Any]) -> str:
        role = current_user.get("role")
        if role is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Role not found in token payload.",
            )
        return role

    def _get_user_id(self, current_user: Dict[str, Any]) -> int:
        user_id = current_user.get("user_id")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="user_id not found in token payload.",
            )
        return int(user_id)

    def _ensure_authenticated(self, current_user: Dict[str, Any]) -> None:
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required.",
            )

    def _ensure_admin_cannot_manage_admin_like(
        self,
        requester_role: str,
        target_role: str,
        operation: str,
    ) -> None:
        """
        Prevent ADMIN from managing ADMIN/SUPERADMIN users.

        High-level access control (who can call the endpoint) is handled
        in the router with RoleChecker.
        """
        if (
            requester_role == UserRole.ADMIN.value
            and target_role in ADMIN_LIKE_ROLES
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Admins are not allowed to {operation} admin-like users.",
            )

    # ---------- Email / password helpers ----------

    def _hash_password(self, plain_password: str) -> str:
        return pwd_hasher.hash(plain_password)

    async def _ensure_email_unique(
        self,
        email: str,
        exclude_user_id: Optional[int] = None,
    ) -> None:
        stmt = select(User).where(
            User.email == email,
            User.is_active == True,  # noqa: E712
        )
        if exclude_user_id is not None:
            stmt = stmt.where(User.id != exclude_user_id)

        result = await self.session.execute(stmt)
        existing = result.scalars().first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is already in use.",
            )

    # ---------- Basic queries ----------

    async def _get_user_by_id(self, user_id: int) -> Optional[User]:
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    # ---------- Public methods ----------

    async def list_users(
        self,
        current_user: Dict[str, Any],
        role: Optional[str],
        company_id: Optional[int],
        search: Optional[str],
    ) -> List[User]:
        """
        Return a list of active users with optional filters.

        Pagination is handled by fastapi-pagination in the router.
        """
        self._ensure_authenticated(current_user)

        stmt = select(User).where(User.is_active == True)  # noqa: E712

        if role:
            stmt = stmt.where(User.role == role)

        if search:
            like_pattern = f"%{search}%"
            stmt = stmt.where(
                (User.full_name.ilike(like_pattern))
                | (User.username.ilike(like_pattern))
            )

        if company_id is not None:
            stmt = (
                stmt.join(CompanyStaff, CompanyStaff.user_id == User.id)
                .where(CompanyStaff.company_id == company_id)
            )

        result = await self.session.execute(stmt)
        users = result.scalars().all()
        return cast(List[User], users)

    async def get_user_detail(
        self,
        current_user: Dict[str, Any],
        user_id: int,
    ) -> User:
        """Return a single active user, enforcing visibility rules."""
        self._ensure_authenticated(current_user)
        requester_role = self._get_role(current_user)
        requester_id = self._get_user_id(current_user)

        user = await self._get_user_by_id(user_id)

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        # Non admin-like users can only view their own profile
        if requester_role not in ADMIN_LIKE_ROLES and requester_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to view this user.",
            )

        return user

    async def create_user(
        self,
        current_user: Dict[str, Any],
        payload: UserCreateRequest,
    ) -> User:
        """
        Create a new user with business RBAC and email uniqueness rules.

        Router ensures only SUPERADMIN/ADMIN can access this endpoint.
        """
        self._ensure_authenticated(current_user)

        requester_role = self._get_role(current_user)
        requester_id = self._get_user_id(current_user)
        requested_role = payload.role

        self._ensure_admin_cannot_manage_admin_like(
            requester_role=requester_role,
            target_role=requested_role,
            operation="create",
        )

        await self._ensure_email_unique(payload.email)

        password_hash = self._hash_password(payload.password)

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

        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)

        return user

    async def update_user(
        self,
        current_user: Dict[str, Any],
        user_id: int,
        payload: UserUpdateRequest,
    ) -> User:
        """Update an existing user, enforcing business rules and email uniqueness."""
        self._ensure_authenticated(current_user)

        requester_role = self._get_role(current_user)
        requester_id = self._get_user_id(current_user)

        user = await self._get_user_by_id(user_id)

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        if requester_role not in ADMIN_LIKE_ROLES:
            # Non admin-like users can only update themselves with limited fields
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
            # Admin / Superadmin
            self._ensure_admin_cannot_manage_admin_like(
                requester_role=requester_role,
                target_role=user.role,
                operation="update",
            )

            if payload.role is not None:
                self._ensure_admin_cannot_manage_admin_like(
                    requester_role=requester_role,
                    target_role=payload.role,
                    operation="assign role to",
                )

        if payload.email is not None and payload.email != user.email:
            await self._ensure_email_unique(
                email=payload.email,
                exclude_user_id=user_id,
            )

        update_data = payload.model_dump(exclude_none=True)
        for key, value in update_data.items():
            setattr(user, key, value)

        user.last_update = datetime.now()

        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def soft_delete_user(
        self,
        current_user: Dict[str, Any],
        user_id: int,
    ) -> None:
        """
        Soft delete a user by setting is_active = False.

        Router already restricts access to SUPERADMIN/ADMIN via RoleChecker.
        """
        self._ensure_authenticated(current_user)

        requester_role = self._get_role(current_user)

        user = await self._get_user_by_id(user_id)

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        self._ensure_admin_cannot_manage_admin_like(
            requester_role=requester_role,
            target_role=user.role,
            operation="delete",
        )

        user.is_active = False
        self.session.add(user)
        await self.session.commit()
