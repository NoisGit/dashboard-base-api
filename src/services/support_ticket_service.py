"""Support ticket service module for the Sentinel Enterprise API"""

# pylint: disable=singleton-comparison

from typing import List, Optional, cast

from fastapi import HTTPException, status
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.models import SupportTicket
from src.schemas import (
    SupportTicketCreateRequest,
    SupportTicketUpdateRequest,
    SupportTicketResponse,
)


class SupportTicketService:
    """Service for support ticket operations"""

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def _get_support_ticket_by_id(
        self,
        ticket_id: int,
    ) -> Optional[SupportTicketResponse]:
        return await self.session.get(SupportTicket, ticket_id)

    async def list_support_tickets(
        self,
        params: Params,
    ) -> Page[SupportTicketResponse]:
        """List active support tickets"""
        stmt = select(SupportTicket).where(SupportTicket.status == True)  # noqa: E712

        return await paginate(
            self.session,
            stmt,
            params,
            transformer=lambda items: [
                SupportTicketResponse(
                    id=ticket.id,
                    title=ticket.title,
                    description=ticket.description,
                    media_name=ticket.media_name,
                    status=ticket.status,
                    created_by=ticket.created_by,
                    created_at=ticket.created_at,
                )
                for ticket in cast(List[SupportTicket], items)
            ],
        )

    async def get_support_ticket_detail(
        self,
        ticket_id: int,
    ) -> SupportTicket:
        """Get a single active support ticket by ID"""
        ticket = await self._get_support_ticket_by_id(ticket_id)
        if not ticket or not ticket.status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Support ticket not found",
            )

        return ticket

    async def create_support_ticket(
        self,
        user_id: int,
        payload: SupportTicketCreateRequest,
    ) -> SupportTicket:
        """Create a new support ticket"""
        ticket = SupportTicket(
            title=payload.title,
            description=payload.description,
            media_name=payload.media_name,
            status=payload.status,
            created_by=user_id,
        )

        self.session.add(ticket)
        await self.session.commit()
        await self.session.refresh(ticket)
        return ticket

    async def update_support_ticket(
        self,
        ticket_id: int,
        payload: SupportTicketUpdateRequest,
    ) -> SupportTicket:
        """Update an existing support ticket"""
        ticket = await self._get_support_ticket_by_id(ticket_id)
        if not ticket or not ticket.status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Support ticket not found",
            )

        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(ticket, key, value)

        await self.session.commit()
        await self.session.refresh(ticket)
        return ticket

    async def soft_delete_support_ticket(
        self,
        ticket_id: int,
    ):
        """Soft delete a support ticket by setting status = False"""
        ticket = await self._get_support_ticket_by_id(ticket_id)
        if not ticket or not ticket.status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Support ticket not found",
            )

        ticket.status = False
        await self.session.commit()
