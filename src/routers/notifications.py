"""Router for Locentr in-app notifications."""

from fastapi import APIRouter, Depends, status
from fastapi_pagination import Page, Params

from src.auth.permissions import RoleChecker
from src.core.enums import UserRole
from src.dependencies import get_notification_service
from src.auth.utils import get_user_id_from_token
from src.services.notification_service import NotificationService

from src.schemas import (
    SimpleNoticationRequest,
    NotificationResponse,
    NotificationMessageResponse,
)


router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.post("/send-all-users", response_model=NotificationResponse)
async def send_notification_to_all_users(
    notification_data: SimpleNoticationRequest,
    notification_service: NotificationService = Depends(
        get_notification_service),
    requester_id=Depends(RoleChecker([UserRole.SUPERADMIN]))
):
    """Create an in-app notification for every active user."""
    notification_response = await notification_service.send_notification_to_all_users(
        notification=notification_data,
        created_by_user_id=requester_id,
    )
    return notification_response


@router.get("/me/unread", response_model=Page[NotificationMessageResponse])
async def me_unread_notifications(
    params: Params = Depends(),
    service: NotificationService = Depends(get_notification_service),
    user_id: int = Depends(get_user_id_from_token)
):
    """Get count of unread notifications for current user"""
    unread_notifications = await service.get_unread_notifications_for_user(user_id, params)
    return unread_notifications


@router.put("/me/mark-read/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def mark_notification_as_read(
    notification_id: int,
    service: NotificationService = Depends(get_notification_service),
    user_id: int = Depends(get_user_id_from_token),
):
    """Mark a specific notification as read for the current user"""
    await service.mark_notification_as_read(user_id, notification_id)
