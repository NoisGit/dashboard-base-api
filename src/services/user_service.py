"""User service module for Sentinel Enterprise API."""

# pylint: disable=no-member, singleton-comparison

from datetime import datetime
from typing import List, Optional, cast

from argon2 import PasswordHasher
from fastapi import HTTPException, status
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.sqlalchemy import paginate as sqlalchemy_paginate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.core.enums import UserRole
from src.models import User, CompanyStaff
from src.schemas import UserCreateRequest, UserUpdateRequest, UserResponse

ADMIN_LIKE_ROLES: set[UserRole] = {
    UserRole.ADMIN,
    UserRole.SUPERADMIN,
}

pwd_hasher = PasswordHasher()


class UserService:
    """Service for user operations and RBAC rules."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

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

    async def _get_user_by_id(self, user_id: int) -> Optional[User]:
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Public helper to retrieve a user by ID (used by other services)."""
        return await self._get_user_by_id(user_id)

    async def list_users(
        self,
        role: Optional[UserRole],
        company_id: Optional[int],
        search: Optional[str],
        params: Params,
    ) -> Page[UserResponse]:
        """Return active users with optional filters."""
        stmt = select(User).where(User.is_active == True)  # noqa: E712

        if role is not None:
            stmt = stmt.where(User.role == role)

        if search:
            like_pattern = f"%{search}%"
            stmt = stmt.where(
                (User.full_name.ilike(like_pattern))
                | (User.username.ilike(like_pattern)),
            )

        if company_id is not None:
            stmt = (
                stmt.join(CompanyStaff, CompanyStaff.user_id == User.id)
                .where(CompanyStaff.company_id == company_id)
            )

        return await sqlalchemy_paginate(
            self.session,
            stmt,
            params,
            transformer=lambda items: [
                UserResponse.model_validate(user)
                for user in cast(List[User], items)
            ],
        )

    async def get_user_detail(
        self,
        requester_id: int,
        requester_role: UserRole,
        user_id: int,
    ) -> User:
        """Return a single active user, enforcing visibility rules."""
        user = await self._get_user_by_id(user_id)

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        if requester_role not in ADMIN_LIKE_ROLES and requester_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to view this user.",
            )

        return user

    async def create_user(
        self,
        payload: UserCreateRequest,
    ) -> User:
        """Create a new user."""
        requested_role = payload.role

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
            created_at=datetime.now(),
        )

        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)

        return user

    async def update_user(
        self,
        requester_id: int,
        requester_role: UserRole,
        user_id: int,
        payload: UserUpdateRequest,
    ) -> User:
        """Update an existing user, enforcing business rules and email uniqueness."""
        user = await self._get_user_by_id(user_id)

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        if requester_role not in ADMIN_LIKE_ROLES:
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
        requester_role: UserRole,
        user_id: int,
    ):
        """Soft delete a user by setting is_active = False."""
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
