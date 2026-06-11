"""Auth service module for Locentr API."""

from datetime import datetime, timedelta
import hashlib
import hmac
from typing import Optional
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.auth import create_token_pair, create_access_token
from src.auth.utils import get_user_id_from_refresh_token
from src.config.config import settings
from src.core.enums import UserRole
from src.models import User
from src.schemas import (
    UserLoginRequest,
    OperatorLoginRequest,
    RefreshTokenRequest,
    AuthTokenResponse,
    AccessTokenResponse,
    AuthRecoveryPasswordRequest,
    AuthResetPasswordRequest,
)
from src.services.email_service import EmailService

ph = PasswordHasher()


class AuthService:
    """Service for user operations."""

    def __init__(self,
                 email_service: EmailService,
                 session: AsyncSession) -> None:
        self.session = session
        self.email_service = email_service

    def _hash_password(self, plain_password: str) -> str:
        return ph.hash(plain_password)

    @staticmethod
    def _digest_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def _verify_password(self, password_hash: str, plain_password: str) -> None:
        try:
            ph.verify(password_hash, plain_password)
        except VerifyMismatchError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            ) from exc

    async def _rehash_password_if_needed(
        self,
        user: User,
        plain_password: str,
    ) -> None:
        if not ph.check_needs_rehash(user.password_hash):
            return

        user.password_hash = ph.hash(plain_password)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)

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

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        statement = select(User).where(User.username == username)
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

    async def login_user(self, user_data: UserLoginRequest) -> AuthTokenResponse:
        """Authenticate user and return token pair"""
        user = await self.get_user_by_email(user_data.email)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        self._verify_password(user.password_hash, user_data.password)

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is suspended",
            )

        await self._rehash_password_if_needed(user, user_data.password)
        await self.update_user_last_login(user.id)

        token_pair = create_token_pair(user.id, user.role)
        user_token_response = AuthTokenResponse(**token_pair)

        await self.update_refresh_token(user.id, user_token_response.refresh_token)

        return user_token_response

    async def login_operator(self, user_data: OperatorLoginRequest) -> AuthTokenResponse:
        """Authenticate operator and return token pair"""
        user = await self.get_user_by_username(user_data.username)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        self._verify_password(user.password_hash, user_data.password)

        if user.role != UserRole.OPERATOR:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unauthorized access",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is suspended",
            )

        await self._rehash_password_if_needed(user, user_data.password)
        await self.update_user_last_login(user.id)

        token_pair = create_token_pair(user.id, user.role)
        user_token_response = AuthTokenResponse(**token_pair)

        await self.update_refresh_token(user.id, user_token_response.refresh_token)

        return user_token_response

    async def _get_user_from_refresh_token(
        self,
        refresh_token: str,
    ) -> User:
        user_id = get_user_id_from_refresh_token(refresh_token)
        user = await self.get_user_by_id(user_id)

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        token_digest = self._digest_token(refresh_token)
        if (
            not user.refresh_token
            or not hmac.compare_digest(user.refresh_token, token_digest)
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        return user

    async def refresh_token(self, refresh_data: RefreshTokenRequest) -> AuthTokenResponse:
        """Refresh access token using a valid refresh token"""
        user = await self._get_user_from_refresh_token(refresh_data.refresh_token)

        token_pair = create_token_pair(user.id, user.role)
        user_token_response = AuthTokenResponse(**token_pair)

        await self.update_refresh_token(user.id, user_token_response.refresh_token)

        return user_token_response

    async def refresh_access_token_only(
        self,
        refresh_data: RefreshTokenRequest
    ) -> AccessTokenResponse:
        """Refresh access token only using a valid refresh token"""
        user = await self._get_user_from_refresh_token(refresh_data.refresh_token)

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

    async def update_refresh_token(self, user_id: int, refresh_token: Optional[str]):
        """Update user's refresh token"""
        user = await self.get_user_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        user.refresh_token = (
            self._digest_token(refresh_token)
            if refresh_token is not None
            else None
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)

    async def logout_user(
        self,
        user_id: int
    ):
        """Logout user details"""
        user = await self.get_user_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        user.refresh_token = None
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)

    async def recovery_password(self, user_data: AuthRecoveryPasswordRequest) -> None:
        """Send recovery instructions without revealing account existence."""
        user = await self.get_user_by_email(user_data.email)

        if not user or not user.is_active:
            return

        current_timestamp = datetime.now()
        reset_token_expiry = current_timestamp + timedelta(minutes=15)
        reset_token = secrets.token_urlsafe(32)

        user.reset_token = self._digest_token(reset_token)
        user.reset_token_expiry = reset_token_expiry
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)

        context_base = {
            "full_name": user.full_name,
            "logo_url": settings.LOGO_URL,
            "reset_url": (
                f"{settings.FRONT_URL_BASE.rstrip('/')}"
                f"/auth/reset-password?token={reset_token}"
            ),
        }

        self.email_service.send_templated_email(
            to_email=user.email,
            subject="Restablece tu contraseña de Locentr",
            template_name="reset_password.html",
            context=context_base,
        )

    async def reset_password(self, user_data: AuthResetPasswordRequest) -> None:
        """Verify reset token and update user password"""
        token_digest = self._digest_token(user_data.reset_token)
        statement = select(User).where(User.reset_token == token_digest)
        result = await self.session.execute(statement)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        if not user.reset_token_expiry or user.reset_token_expiry < datetime.now():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reset token has expired"
            )

        if user_data.new_password != user_data.confirm_new_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password and confirmation do not match"
            )

        new_password_hashed = ph.hash(user_data.new_password)

        user.password_hash = new_password_hashed
        user.reset_token = None
        user.reset_token_expiry = None
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
