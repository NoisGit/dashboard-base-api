"""User service module for Coredeck API."""

# pylint: disable=no-member, singleton-comparison

from datetime import datetime
from typing import List, Optional, cast

from argon2 import PasswordHasher
from fastapi import HTTPException, status
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.core.enums import UserRole
from src.models import User, CompanyStaff
from src.schemas import (
    UserCreateRequest,
    UserUpdateRequest,
    UserSuspendRequest,
    UserResponse,
    UserMeResponse,
    UserChangePasswordRequest,
)

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

    async def _ensure_username_unique(
        self,
        username: str,
    ) -> None:
        stmt = select(User).where(
            User.username == username,
        )

        result = await self.session.execute(stmt)
        existing = result.scalars().first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username is already in use.",
            )

    async def _get_user_by_id(self, user_id: int) -> Optional[User]:
        return await self.session.get(User, user_id)

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Public helper to retrieve a user by ID (used by other services)."""
        return await self._get_user_by_id(user_id)

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalars().first()

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

    async def update_refresh_token(
        self,
        user_id: int,
        refresh_token: Optional[str]
    ):
        """Update user's refresh token"""
        user = await self.get_user_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        user.refresh_token = refresh_token
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

        return await paginate(
            self.session,
            stmt,
            params,
            transformer=lambda items: [
                UserResponse(
                    id=user.id,
                    username=user.username,
                    full_name=user.full_name,
                    email=user.email,
                    role=user.role,
                    status=user.status,
                    is_active=user.is_active,
                    plan_id=user.plan_id,
                    created_at=user.created_at,
                )
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
        await self._ensure_username_unique(payload.username)

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

    async def suspend_user(
        self,
        user_id: int,
        payload: UserSuspendRequest,
    ) -> None:
        """Suspend user by setting is_active = False and saving reason/date."""
        user = await self._get_user_by_id(user_id)

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        user.is_active = False
        user.date_change_status = datetime.now()
        user.reason_suspension = payload.reason_suspension

        self.session.add(user)
        await self.session.commit()

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

    async def get_user_profile(
        self,
        user_id: int,
    ) -> UserMeResponse:
        """Return current user profile for /auth/me."""
        user = await self._get_user_by_id(user_id)

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        stmt = select(CompanyStaff.company_id).where(
            CompanyStaff.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        company_row = result.first()
        company_id = company_row[0] if company_row else None

        return UserMeResponse(
            id=user.id,
            full_name=user.full_name,
            email=user.email,
            role=user.role,
            company_id=company_id,
            avatar=None,
        )

    async def verify_user_password(
        self,
        user_id: int,
        password: str,
    ) -> bool:
        """Verify user's password"""
        user = await self.get_user_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        if not ph.verify(user.password_hash, password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        return True

    async def change_user_password(
        self,
        user_id: int,
        payload: UserChangePasswordRequest,
    ):
        """Change password for authenticated user"""
        await self.verify_user_password(
            user_id=user_id,
            password=payload.current_password,
        )

        if payload.new_password != payload.confirm_new_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password and confirmation do not match",
            )

        await self.update_user_password(
            user_id=user_id,
            new_password=payload.new_password,
        )

        await self.update_refresh_token(
            user_id=user_id,
            refresh_token=None,
        )

    async def get_all_fcm_tokens(self) -> List[str]:
        """Get FCM tokens of all users"""
        result = await self.session.execute(
            select(User.fcm_token)
            .where(User.fcm_token != None)  # pylint: disable=singleton-comparison
        )
        tokens = result.scalars().all()
        return tokens
