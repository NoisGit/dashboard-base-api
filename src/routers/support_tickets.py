"""Support ticket router module for Coredeck API"""

from typing import Optional

from fastapi import APIRouter, Depends, status, Query
from fastapi_pagination import Page, Params

from src.auth.permissions import RoleChecker
from src.core.enums import UserRole, SupportTicketStatus
from src.dependencies import get_support_ticket_service
from src.schemas import (
    SupportTicketCreateRequest,
    SupportTicketUpdateRequest,
    SupportTicketResponse,
    SupportTicketCommentCreateRequest,
    SupportTicketCommentUpdateRequest,
    SupportTicketCommentResponse,
)
from src.services.support_ticket_service import SupportTicketService

router = APIRouter(
    prefix="/support-tickets",
    tags=["support-tickets"],
)


@router.get(
    "/all",
    response_model=Page[SupportTicketResponse],
)
async def list_all_support_tickets(
    params: Params = Depends(),
    status_filter: Optional[SupportTicketStatus] = Query(None, alias="status"),
    service: SupportTicketService = Depends(get_support_ticket_service),
    _=Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
            ],
        ),
    ),
) -> Page[SupportTicketResponse]:
    """List support tickets"""
    tickets = await service.list_support_tickets(
        params=params,
        status_filter=status_filter,
    )
    return tickets


@router.get(
    "/me",
    response_model=Page[SupportTicketResponse],
)
async def list_my_support_tickets(
    params: Params = Depends(),
    status_filter: Optional[SupportTicketStatus] = Query(None, alias="status"),
    service: SupportTicketService = Depends(get_support_ticket_service),
    user_id: int = Depends(
        RoleChecker(
            [
                UserRole.ADMIN,
            ],
        ),
    ),
) -> Page[SupportTicketResponse]:
    """List support tickets"""
    tickets = await service.list_support_tickets(
        params=params,
        status_filter=status_filter,
        is_owner_user_id=user_id,
        excluded_statuses=[
            SupportTicketStatus.CANCELED,
            SupportTicketStatus.CLOSED,
        ],
    )
    return tickets


@router.get(
    "/{ticket_id}",
    response_model=SupportTicketResponse,
)
async def get_support_ticket_detail(
    ticket_id: int,
    service: SupportTicketService = Depends(get_support_ticket_service),
    user_id: int = Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
                UserRole.ADMIN,
            ],
        ),
    ),
) -> SupportTicketResponse:
    """Get a single support ticket by ID"""
    ticket = await service.get_support_ticket_detail(
        ticket_id=ticket_id,
        user_id=user_id,
    )
    return ticket


@router.post(
    "/",
    response_model=SupportTicketResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_support_ticket(
    payload: SupportTicketCreateRequest,
    service: SupportTicketService = Depends(get_support_ticket_service),
    user_id: int = Depends(
        RoleChecker(
            [
                UserRole.ADMIN,
            ],
        ),
    ),
) -> SupportTicketResponse:
    """Create a new support ticket"""
    ticket = await service.create_support_ticket(
        user_id=user_id,
        payload=payload,
    )
    return ticket


@router.put(
    "/{ticket_id}",
    response_model=SupportTicketResponse,
)
async def update_support_ticket(
    ticket_id: int,
    payload: SupportTicketUpdateRequest,
    service: SupportTicketService = Depends(get_support_ticket_service),
    user_id: int = Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
                UserRole.ADMIN,
            ],
        ),
    ),
) -> SupportTicketResponse:
    """Update an existing support ticket"""
    ticket = await service.update_support_ticket(
        user_id=user_id,
        ticket_id=ticket_id,
        payload=payload,
    )
    return ticket


@router.delete(
    "/{ticket_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_support_ticket(
    ticket_id: int,
    service: SupportTicketService = Depends(get_support_ticket_service),
    user_id: int = Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
                UserRole.ADMIN,
            ],
        ),
    ),
):
    """Soft delete a support ticket"""
    await service.soft_delete_support_ticket(
        user_id=user_id,
        ticket_id=ticket_id,
    )


@router.get(
    "/{ticket_id}/comments",
    response_model=list[SupportTicketCommentResponse],
)
async def list_support_ticket_comments(
    ticket_id: int,
    service: SupportTicketService = Depends(get_support_ticket_service),
    user_id: int = Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
                UserRole.ADMIN,
            ],
        ),
    ),
) -> list[SupportTicketCommentResponse]:
    """List support ticket comments"""
    comments = await service.list_support_ticket_comments(
        user_id=user_id,
        ticket_id=ticket_id,
    )
    return comments


@router.get(
    "/{ticket_id}/comments/{comment_id}",
    response_model=SupportTicketCommentResponse,
)
async def get_support_ticket_comment_detail(
    ticket_id: int,
    comment_id: int,
    service: SupportTicketService = Depends(get_support_ticket_service),
    user_id: int = Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
                UserRole.ADMIN,
            ],
        ),
    ),
) -> SupportTicketCommentResponse:
    """Get support ticket comment by ID"""
    comment = await service.get_support_ticket_comment_detail(
        user_id=user_id,
        ticket_id=ticket_id,
        comment_id=comment_id,
    )
    return comment


@router.post(
    "/{ticket_id}/comments",
    response_model=SupportTicketCommentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_support_ticket_comment(
    ticket_id: int,
    payload: SupportTicketCommentCreateRequest,
    service: SupportTicketService = Depends(get_support_ticket_service),
    user_id: int = Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
                UserRole.ADMIN,
            ],
        ),
    ),
) -> SupportTicketCommentResponse:
    """Create support ticket comment"""
    comment = await service.create_support_ticket_comment(
        ticket_id=ticket_id,
        user_id=user_id,
        payload=payload,
    )
    return comment


@router.put(
    "/{ticket_id}/comments/{comment_id}",
    response_model=SupportTicketCommentResponse,
)
async def update_support_ticket_comment(
    ticket_id: int,
    comment_id: int,
    payload: SupportTicketCommentUpdateRequest,
    service: SupportTicketService = Depends(get_support_ticket_service),
    user_id: int = Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
                UserRole.ADMIN,
            ],
        ),
    ),
) -> SupportTicketCommentResponse:
    """Update support ticket comment"""
    comment = await service.update_support_ticket_comment(
        user_id=user_id,
        ticket_id=ticket_id,
        comment_id=comment_id,
        payload=payload,
    )
    return comment


@router.delete(
    "/{ticket_id}/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_support_ticket_comment(
    ticket_id: int,
    comment_id: int,
    service: SupportTicketService = Depends(get_support_ticket_service),
    user_id: int = Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
                UserRole.ADMIN,
            ],
        ),
    ),
):
    """Delete support ticket comment"""
    await service.delete_support_ticket_comment(
        user_id=user_id,
        ticket_id=ticket_id,
        comment_id=comment_id,
    )
