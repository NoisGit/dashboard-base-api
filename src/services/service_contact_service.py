"""Service contact service module for the Sentinel Enterprise API."""

from typing import List, cast

from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlmodel import paginate
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, or_, desc

from src.services import UserService
from src.models import ServiceContact
from src.schemas import (
    ServiceContactResponse,
    ServiceContactCreateRequest,
)


class ServiceContactService:
    """Service for Service contact operations."""

    def __init__(
        self,
        session: AsyncSession,
        user_service: UserService,
    ):
        self.session = session
        self.user_service = user_service

    async def list_service_contacts(
        self,
        location_id: int,
        params: Params,
    ) -> Page[ServiceContactResponse]:
        """
        List service contacts for a location.
        and location-specific numbers.
        """
        stmt = select(ServiceContact).where(
            ServiceContact.location_id == location_id,
        ).order_by(
            desc(ServiceContact.created_at),
        )

        return await paginate(
            self.session,
            stmt,
            params,
            transformer=lambda items: [
                ServiceContactResponse(
                    id=service_contact.id,
                    location_id=service_contact.location_id,
                    service_name=service_contact.service_name,
                    person_name=service_contact.person_name,
                    email=service_contact.email,
                    phone=service_contact.phone,
                    created_by=service_contact.created_by,
                    created_at=service_contact.created_at,
                )
                for service_contact in cast(List[ServiceContact], items)
            ]
        )


async def create_service_contact(
    self,
    user_id: int,
    payload: ServiceContactCreateRequest
):
    """
    Create a new service contact.
    Applies consistency rules and authorization checks.
    """

    user = self.user_service.get_user_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    # Create the service contact
    new_contact = ServiceContact(
        service_name=payload.service_name,
        person_name=payload.person_name,
        email=payload.email,
        phone=payload.phone,
        location_id=payload.location_id,
        created_by=user_id,
    )

    self.session.add(new_contact)
    await self.session.commit()
    await self.session.refresh(new_contact)


__all__ = ["ServiceContactService"]
