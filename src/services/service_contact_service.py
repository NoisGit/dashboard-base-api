"""Service contact service module for the Sentinel Enterprise API."""

from typing import List, cast

from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlmodel import paginate
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, or_, desc

from src.core.enums import UserRole
from src.services import UserService
from src.services import LocationService
from src.models import ServiceContact, CompanyStaff
from src.schemas import (
    ServiceContactResponse,
    ServiceContactCreateRequest,
    ServiceContactUpdateRequest,
)


class ServiceContactService:
    """Service for Service contact operations."""

    def __init__(
        self,
        session: AsyncSession,
        user_service: UserService,
        location_service: LocationService,
    ):
        self.session = session
        self.user_service = user_service
        self.location_service = location_service

    async def get_service_contact_by_id(
        self,
        service_contact_id: int,
    ) -> ServiceContact:
        """Get service contact by ID."""
        stmt = select(ServiceContact) \
            .where(ServiceContact.id == service_contact_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def list_service_contacts(
        self,
        location_id: int,
        user_id: int,
        params: Params,
    ) -> Page[ServiceContactResponse]:
        """
        List service contacts for a location.
        and location-specific numbers.
        """
        user_has_permission = await self.location_service.check_user_permission_on_location(
            user_id=user_id,
            location_id=location_id,
        )

        if not user_has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view contacts for this location.",
            )

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

        user = await self.user_service.get_user_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        location = await self.location_service.get_location_by_id(payload.location_id)
        if not location:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Location not found.",
            )

        if user.role != UserRole.SUPERADMIN:
            if location.created_by != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to create a contact in this location.",
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

    async def update_service_contact(
        self,
        user_id: int,
        service_contact_id: int,
        payload: ServiceContactUpdateRequest
    ):
        """
        Update an existing service contact.
        Applies consistency rules and authorization checks.
        """

        user = await self.user_service.get_user_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        service_contact = await self.get_service_contact_by_id(service_contact_id)

        if not service_contact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Service contact with id {service_contact_id} not found.",
            )

        if user.role != UserRole.SUPERADMIN:
            if service_contact.created_by != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to edit this contact.",
                )

        contact_model = payload.model_dump(exclude_none=True)
        for key, value in contact_model.items():
            setattr(service_contact, key, value)

        await self.session.commit()
        await self.session.refresh(service_contact)

    async def delete_service_contact(
        self,
        user_id: int,
        service_contact_id: int,
    ) -> None:
        """
        Delete an existing service contact.
        Applies consistency rules and authorization checks.
        """

        user = await self.user_service.get_user_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        service_contact = await self.get_service_contact_by_id(service_contact_id)

        if not service_contact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Service contact with id {service_contact_id} not found.",
            )

        if user.role != UserRole.SUPERADMIN:
            if service_contact.created_by != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to delete this contact.",
                )

        await self.session.delete(service_contact)
        await self.session.commit()


__all__ = ["ServiceContactService"]
