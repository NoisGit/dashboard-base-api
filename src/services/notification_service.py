"""Notification service for Locentr API."""

from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, desc

from src.models import Notification, User
from src.schemas import (
    SimpleNoticationRequest,
    NotificationResponse,
    NotificationMessageResponse,
)
from src.services.user_service import UserService


class NotificationService:
    """Service for notification operations."""

    def __init__(
        self,
        session: AsyncSession,
        user_service: UserService,
    ):
        self.session = session
        self.user_service = user_service

    async def create_notification(
        self,
        user_id: int,
        notification: SimpleNoticationRequest,
        created_by_user_id: int,
    ):
        """Create a new notification record."""
        notification = Notification(
            title=notification.title,
            message=notification.message,
            created_by_user_id=created_by_user_id,
            user_id=user_id,
        )
        self.session.add(notification)
        await self.session.commit()
        await self.session.refresh(notification)

    async def get_notification_by_id(
        self,
        notification_id: int,
    ) -> Optional[Notification]:
        """Retrieve a notification by ID."""
        result = await self.session.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        return result.scalar_one_or_none()

    async def mark_notification_as_read(
        self,
        user_id: int,
        notification_id: int,
    ):
        """Mark a notification as read."""
        notification = await self.get_notification_by_id(notification_id)

        if not notification or notification.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found",
            )

        notification.read_at = datetime.now()
        self.session.add(notification)
        await self.session.commit()
        await self.session.refresh(notification)

    async def get_notifications_for_user(
        self,
        user_id: int,
        params: Params = Params(),
    ) -> Page[NotificationMessageResponse]:
        """Get paginated notifications for a user."""
        query = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(desc(Notification.created_at))
        )

        return await paginate(
            self.session,
            query,
            params,
            transformer=lambda items: [
                NotificationMessageResponse(
                    id=notification.id,
                    title=notification.title,
                    message=notification.message,
                    read_at=notification.read_at,
                    created_at=notification.created_at,
                ) for notification in items
            ],
        )

    async def get_unread_notifications_for_user(
        self,
        user_id: int,
        params: Params = Params(),
    ) -> Page[NotificationMessageResponse]:
        """Get paginated unread notifications for a user."""
        query = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .where(Notification.read_at == None)  # pylint: disable=singleton-comparison
            .order_by(desc(Notification.created_at))
        )

        return await paginate(
            self.session,
            query,
            params,
            transformer=lambda items: [
                NotificationMessageResponse(
                    id=notification.id,
                    title=notification.title,
                    message=notification.message,
                    read_at=notification.read_at,
                    created_at=notification.created_at,
                ) for notification in items
            ],
        )

    async def send_notification_to_all_users(
        self,
        notification: SimpleNoticationRequest,
        created_by_user_id: int,
    ) -> NotificationResponse:
        """Create an in-app notification for every active user."""
        result = await self.session.execute(
            select(User.id).where(User.is_active == True)  # noqa: E712
        )
        user_ids = result.scalars().all()
        for user_id in user_ids:
            self.session.add(
                Notification(
                    title=notification.title,
                    message=notification.message,
                    created_by_user_id=created_by_user_id,
                    user_id=user_id,
                )
            )
        await self.session.commit()

        return NotificationResponse(
            success=len(user_ids),
            failed=0,
        )
