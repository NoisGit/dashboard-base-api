"""Router for managing notifications, including sending push notifications"""

from fastapi import APIRouter, Depends, status
from fastapi_pagination import Page, Params

from src.auth.permissions import RoleChecker
from src.core.enums import UserRole
from src.dependencies import get_notification_service
from src.auth.utils import get_user_id_from_token, get_current_user
from src.services.notification_service import NotificationService

from src.schemas import (
    SimpleNoticationRequest,
    NotificationResponse,
    NotificationMessageResponse,
)


router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/send-all-users", response_model=NotificationResponse)
async def send_notification_to_all_users(
    notification_data: SimpleNoticationRequest,
    notification_service: NotificationService = Depends(
        get_notification_service),
    _=Depends(RoleChecker([UserRole.SUPERADMIN]))
):
    """Send push notification to all users"""
    notification_response = await notification_service.send_notification_to_all_users(
        title=notification_data.title,
        message=notification_data.message,
    )
    return notification_response


@router.post("/me/unread", response_model=Page[NotificationMessageResponse])
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
    _: int = Depends(get_current_user)
):
    """Mark a specific notification as read for the current user"""
    await service.mark_notification_as_read(notification_id)
