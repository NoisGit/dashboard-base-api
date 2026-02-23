"""Support ticket service module for the Sentinel Enterprise API"""

# pylint: disable=singleton-comparison

from datetime import datetime
from typing import List, Optional, cast

from fastapi import HTTPException, status
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.core.enums import SupportTicketStatus, UserRole
from src.models import SupportTicket
from src.models.support_response import SupportResponse
from src.schemas import (
    SupportTicketCreateRequest,
    SupportTicketUpdateRequest,
    SupportTicketResponse,
    SupportTicketCommentCreateRequest,
    SupportTicketCommentUpdateRequest,
    SupportTicketCommentResponse,
)
from src.services import UserService, AzureService


class SupportTicketService:
    """Service for support ticket operations"""

    def __init__(
        self,
        session: AsyncSession,
        user_service: UserService,
        azure_service: AzureService,
    ):
        self.session = session
        self.user_service = user_service
        self.azure_service = azure_service

    async def _get_support_ticket_by_id(
        self,
        ticket_id: int,
    ) -> Optional[SupportTicket]:
        stmt = select(SupportTicket).where(SupportTicket.id == ticket_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def _get_support_ticket_comment_by_id(
        self,
        ticket_id: int,
        comment_id: int,
    ) -> Optional[SupportResponse]:
        stmt = (
            select(SupportResponse)
            .where(SupportResponse.ticket_id == ticket_id)
            .where(SupportResponse.id == comment_id)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def _get_user_or_404(self, user_id: int):
        user = await self.user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return user

    async def list_support_tickets(
        self,
        params: Params,
        status_filter: Optional[SupportTicketStatus],
        is_owner_user_id: Optional[int] = None,
        excluded_statuses: Optional[List[SupportTicketStatus]] = None,
    ) -> Page[SupportTicketResponse]:
        """List support tickets with status filter"""
        stmt = select(SupportTicket)

        if is_owner_user_id is not None:
            stmt = stmt.where(SupportTicket.created_by == is_owner_user_id)

        if excluded_statuses:
            stmt = stmt.where(
                SupportTicket.status.notin_(  # pylint: disable=no-member
                    excluded_statuses)
            )

        if status_filter is not None:
            stmt = stmt.where(SupportTicket.status == status_filter)

        return await paginate(
            self.session,
            stmt,
            params,
            transformer=lambda items: [
                SupportTicketResponse(
                    id=ticket.id,
                    title=ticket.title,
                    description=ticket.description,
                    media_name=self.azure_service.generate_read_sas_url(
                        container_name="support-tickets",
                        blob_name=ticket.media_name,
                    ) if ticket.media_name else None,
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
        user_id: int,
    ) -> SupportTicketResponse:
        """Get a single support ticket by ID"""
        ticket = await self.check_user_permission_on_ticket(user_id, ticket_id)
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Support ticket not found",
            )

        return SupportTicketResponse(
            id=ticket.id,
            title=ticket.title,
            description=ticket.description,
            media_name=self.azure_service.generate_read_sas_url(
                container_name="support-tickets",
                blob_name=ticket.media_name,
            ) if ticket.media_name else None,
            status=ticket.status,
            created_by=ticket.created_by,
            created_at=ticket.created_at,
        )

    async def create_support_ticket(
        self,
        user_id: int,
        payload: SupportTicketCreateRequest,
    ) -> SupportTicketResponse:
        """Create a new support ticket"""
        ticket = SupportTicket(
            title=payload.title,
            description=payload.description,
            media_name=payload.media_name,
            status=SupportTicketStatus.OPEN,
            created_by=user_id,
        )

        self.session.add(ticket)
        await self.session.commit()
        await self.session.refresh(ticket)

        return SupportTicketResponse(
            id=ticket.id,
            title=ticket.title,
            description=ticket.description,
            media_name=self.azure_service.generate_read_sas_url(
                container_name="support-tickets",
                blob_name=ticket.media_name,
            ) if ticket.media_name else None,
            status=ticket.status,
            created_by=ticket.created_by,
            created_at=ticket.created_at,
        )

    async def update_support_ticket(
        self,
        ticket_id: int,
        payload: SupportTicketUpdateRequest,
    ) -> SupportTicketResponse:
        """Update an existing support ticket"""
        ticket = await self._get_support_ticket_by_id(ticket_id)
        if not ticket or ticket.status == SupportTicketStatus.CANCELED:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Support ticket not found",
            )

        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(ticket, key, value)

        await self.session.commit()
        await self.session.refresh(ticket)

        return SupportTicketResponse(
            id=ticket.id,
            title=ticket.title,
            description=ticket.description,
            media_name=self.azure_service.generate_read_sas_url(
                container_name="support-tickets",
                blob_name=ticket.media_name,
            ) if ticket.media_name else None,
            status=ticket.status,
            created_by=ticket.created_by,
            created_at=ticket.created_at,
        )

    async def soft_delete_support_ticket(
        self,
        ticket_id: int,
    ):
        """Soft delete a support ticket by setting status = CANCELED"""
        ticket = await self._get_support_ticket_by_id(ticket_id)
        if not ticket or ticket.status == SupportTicketStatus.CANCELED:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Support ticket not found",
            )

        ticket.status = SupportTicketStatus.CANCELED
        await self.session.commit()

    async def list_support_ticket_comments(
        self,
        ticket_id: int,
    ) -> List[SupportTicketCommentResponse]:
        """List support ticket comments"""
        ticket = await self._get_support_ticket_by_id(ticket_id)
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Support ticket not found",
            )

        stmt = (
            select(SupportResponse)
            .where(SupportResponse.ticket_id == ticket_id)
            .order_by(SupportResponse.created_at)
        )
        result = await self.session.execute(stmt)
        comments = cast(List[SupportResponse], result.scalars().all())

        return [
            SupportTicketCommentResponse(
                id=comment.id,
                ticket_id=comment.ticket_id,
                content=comment.comment,
                created_by=comment.created_by,
                created_at=comment.created_at,
                edited_at=comment.edited_at,
            )
            for comment in comments
        ]

    async def get_support_ticket_comment_detail(
        self,
        ticket_id: int,
        comment_id: int,
    ) -> SupportTicketCommentResponse:
        """Get support ticket comment by ID"""
        ticket = await self._get_support_ticket_by_id(ticket_id)
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Support ticket not found",
            )

        comment = await self._get_support_ticket_comment_by_id(ticket_id, comment_id)
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Support ticket comment not found",
            )

        return SupportTicketCommentResponse(
            id=comment.id,
            ticket_id=comment.ticket_id,
            content=comment.comment,
            created_by=comment.created_by,
            created_at=comment.created_at,
            edited_at=comment.edited_at,
        )

    async def create_support_ticket_comment(
        self,
        ticket_id: int,
        user_id: int,
        payload: SupportTicketCommentCreateRequest,
    ) -> SupportTicketCommentResponse:
        """Create support ticket comment"""
        ticket = await self._get_support_ticket_by_id(ticket_id)
        if not ticket or ticket.status == SupportTicketStatus.CANCELED:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Support ticket not found",
            )

        comment = SupportResponse(
            ticket_id=ticket_id,
            comment=payload.content,
            created_by=user_id,
        )

        self.session.add(comment)
        await self.session.commit()
        await self.session.refresh(comment)

        return SupportTicketCommentResponse(
            id=comment.id,
            ticket_id=comment.ticket_id,
            content=comment.comment,
            created_by=comment.created_by,
            created_at=comment.created_at,
            edited_at=comment.edited_at,
        )

    async def update_support_ticket_comment(
        self,
        user_id: int,
        ticket_id: int,
        comment_id: int,
        payload: SupportTicketCommentUpdateRequest,
    ) -> SupportTicketCommentResponse:
        """Update support ticket comment"""
        user = await self._get_user_or_404(user_id)

        ticket = await self._get_support_ticket_by_id(ticket_id)
        if not ticket or ticket.status == SupportTicketStatus.CANCELED:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Support ticket not found",
            )

        comment = await self._get_support_ticket_comment_by_id(ticket_id, comment_id)
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Support ticket comment not found",
            )

        if user.role != UserRole.SUPERADMIN and comment.created_by != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not allowed",
            )

        update_data = payload.model_dump(exclude_unset=True)
        if "content" in update_data and update_data["content"] is not None:
            comment.comment = update_data["content"]
            comment.edited_at = datetime.now()

        await self.session.commit()
        await self.session.refresh(comment)

        return SupportTicketCommentResponse(
            id=comment.id,
            ticket_id=comment.ticket_id,
            content=comment.comment,
            created_by=comment.created_by,
            created_at=comment.created_at,
            edited_at=comment.edited_at,
        )

    async def delete_support_ticket_comment(
        self,
        user_id: int,
        ticket_id: int,
        comment_id: int,
    ):
        """Delete support ticket comment"""
        user = await self._get_user_or_404(user_id)

        ticket = await self._get_support_ticket_by_id(ticket_id)
        if not ticket or ticket.status == SupportTicketStatus.CANCELED:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Support ticket not found",
            )

        comment = await self._get_support_ticket_comment_by_id(ticket_id, comment_id)
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Support ticket comment not found",
            )

        if user.role != UserRole.SUPERADMIN and comment.created_by != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not allowed",
            )

        await self.session.delete(comment)
        await self.session.commit()

    async def check_user_permission_on_ticket(
        self,
        user_id: int,
        ticket_id: int,
    ) -> SupportTicket:
        """Validate User permission on ticket"""
        ticket = await self._get_support_ticket_by_id(ticket_id)
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Support ticket not found.",
            )

        user = await self.user_service.get_user_by_id(user_id)
        if not user or not getattr(user, "is_active", True):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        is_superadmin = user.role == UserRole.SUPERADMIN

        if is_superadmin:
            return ticket
        else:
            if ticket.created_by == user_id:
                return ticket
            else:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not allowed.",
                )
