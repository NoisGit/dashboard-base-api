"""User service module for Sentinel Enterprise API."""

# pylint: disable=no-member, singleton-comparison

from datetime import datetime
from typing import List, Optional, cast

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import HTTPException, status
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate as sqlalchemy_paginate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from src.auth import create_token_pair, create_access_token
from src.auth.utils import get_user_id_from_refresh_token


from src.core.enums import UserRole
from src.models import User, CompanyStaff
from src.schemas import (
    UserCreateRequest,
    UserUpdateRequest,
    UserLoginRequest,
    RefreshTokenRequest,
    UserResponse,
    UserTokenResponse,
    AccessTokenResponse)

ph = PasswordHasher()


class UserService:
    """Service for user operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _hash_password(self, plain_password: str) -> str:
        return ph.hash(plain_password)

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

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        statement = select(User).where(User.email == email)
        result = await self.session.execute(statement)
        user = result.scalar_one_or_none()
        return user

    async def update_user_password(self, user_id: int, new_password: str):
        """Update user details"""
        user = await self.get_user_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        new_password_hashed = ph.hash(new_password)
        user.password_hash = new_password_hashed
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)

    async def login_user(self, user_data: UserLoginRequest) -> UserTokenResponse:
        """Authenticate user and return token pair"""
        user = await self.get_user_by_email(user_data.email)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        # Verify password match with Argon2 Hash
        try:
            ph.verify(user.password_hash, user_data.password)
        # if password does not match
        except VerifyMismatchError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        # Rehash password if needed
        if ph.check_needs_rehash(user.password_hash):
            user.password_hash = ph.hash(user_data.password)
            await self.update_user_password(user.id, user.password_hash)

        await self.update_user_last_login(user.id)

        token_pair = create_token_pair(user.id, user.role)
        user_token_response = UserTokenResponse(**token_pair)
        return user_token_response

    async def refresh_token(self, refresh_data: RefreshTokenRequest) -> UserTokenResponse:
        """Refresh access token using a valid refresh token"""
        user_id = get_user_id_from_refresh_token(refresh_data.refresh_token)

        user = await self.get_user_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        token_pair = create_token_pair(user.id, user.role)
        user_token_response = UserTokenResponse(**token_pair)
        return user_token_response

    async def refresh_access_token_only(
        self,
        refresh_data: RefreshTokenRequest
    ) -> AccessTokenResponse:
        """Refresh access token only using a valid refresh token"""
        user_id = get_user_id_from_refresh_token(refresh_data.refresh_token)

        user = await self.get_user_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        access_token = create_access_token(user.id, user.role)
        user_access_token = AccessTokenResponse(access_token=access_token)
        return user_access_token

    async def update_user_last_login(self, user_id: int):
        """Update user's last login time"""
        user = await self.get_user_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        user.last_session = datetime.now()
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)

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
        user_id: int,
    ) -> User:
        """Return a single active user."""
        user = await self._get_user_by_id(user_id)

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        return user

    async def create_user(
        self,
        payload: UserCreateRequest,
    ) -> User:
        """Create a new user."""
        await self._ensure_email_unique(payload.email)

        password_hash = self._hash_password(payload.password)

        user = User(
            username=payload.username,
            full_name=payload.full_name,
            email=payload.email,
            password_hash=password_hash,
            role=payload.role,
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
        user_id: int,
        payload: UserUpdateRequest,
    ) -> User:
        """Update an existing user and keep email unique."""
        user = await self._get_user_by_id(user_id)

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
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
        user_id: int,
    ):
        """Soft delete a user by setting is_active = False."""
        user = await self._get_user_by_id(user_id)

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        user.is_active = False
        self.session.add(user)
        await self.session.commit()
