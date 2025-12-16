"""Support ticket router module for Sentinel Enterprise API"""

from fastapi import APIRouter, Depends, status
from fastapi_pagination import Page, Params

from src.auth.utils import get_user_data_from_token, get_user_id_from_token
from src.auth.permissions import RoleChecker
from src.core.enums import UserRole
from src.dependencies import get_support_ticket_service
from src.schemas import (
    SupportTicketCreateRequest,
    SupportTicketUpdateRequest,
    SupportTicketResponse,
)
from src.services.support_ticket_service import SupportTicketService

router = APIRouter(
    prefix="/support-tickets",
    tags=["support_tickets"],
)


@router.get(
    "/",
    response_model=Page[SupportTicketResponse],
)
async def list_support_tickets(
    params: Params = Depends(),
    service: SupportTicketService = Depends(get_support_ticket_service),
    _=Depends(get_user_data_from_token),
) -> Page[SupportTicketResponse]:
    """List active support tickets"""
    tickets = await service.list_support_tickets(
        params=params,
    )
    return tickets


@router.get(
    "/{ticket_id}",
    response_model=SupportTicketResponse,
)
async def get_support_ticket_detail(
    ticket_id: int,
    service: SupportTicketService = Depends(get_support_ticket_service),
    _=Depends(get_user_data_from_token),
) -> SupportTicketResponse:
    """Get a single support ticket by ID"""
    ticket = await service.get_support_ticket_detail(
        ticket_id=ticket_id,
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
    user_id: int = Depends(get_user_id_from_token),
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
    _=Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
                UserRole.ADMIN,
                UserRole.SUBADMIN,
            ],
        ),
    ),
) -> SupportTicketResponse:
    """Update an existing support ticket"""
    ticket = await service.update_support_ticket(
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
    _=Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
                UserRole.ADMIN,
                UserRole.SUBADMIN,
            ],
        ),
    ),
):
    """Soft delete a support ticket by setting status = False"""
    await service.soft_delete_support_ticket(
        ticket_id=ticket_id,
    )
