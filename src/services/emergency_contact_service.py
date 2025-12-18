"""Emergency contact service module for the Sentinel Enterprise API."""

from typing import List, Optional, cast

from fastapi_pagination import Page, paginate, Params
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, or_, desc

from src.core.enums import UserRole
from src.services import UserService
from src.models import EmergencyContact
from src.schemas import (
    EmergencyContactCreateRequest,
    EmergencyContactUpdateRequest,
    EmergencyContactResponse,
)


class EmergencyContactService:
    """Service for emergency contact operations."""

    def __init__(
        self,
        session: AsyncSession,
        user_service: UserService,
    ):
        self.session = session
        self.user_service = user_service

    async def get_emergency_contact_by_id(
        self,
        contact_id: int,
    ) -> Optional[EmergencyContact]:
        """Get emergency contact by ID."""
        stmt = select(EmergencyContact) \
            .where(EmergencyContact.id == contact_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def list_emergency_contacts(
        self,
        params: Params,
        location_id: int,
    ) -> Page[EmergencyContactResponse]:
        """
        List emergency contacts for a location.
        Returns both default country numbers (is_default=TRUE)
        and location-specific numbers.
        """
        stmt = select(EmergencyContact).where(
            or_(
                EmergencyContact.is_default == True,  # pylint: disable=singleton-comparison
                EmergencyContact.location_id == location_id,
            )
        ).order_by(
            desc(EmergencyContact.is_default),
            desc(EmergencyContact.created_at),
        )

        return await paginate(
            self.session,
            stmt,
            params,
            transformer=lambda items: [
                EmergencyContactResponse(
                    id=contact.id,
                    name=contact.name,
                    phone=contact.phone,
                    location_id=contact.location_id,
                    is_default=contact.is_default,
                    created_by=contact.created_by,
                    created_at=contact.created_at,
                )
                for contact in cast(List[EmergencyContact], items)
            ]
        )

    async def get_emergency_contact_detail(
        self,
        contact_id: int,
    ) -> EmergencyContactResponse:
        """Get a single emergency contact by ID."""
        contact = await self.get_emergency_contact_by_id(contact_id)

        if not contact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Emergency contact with id {contact_id} not found.",
            )

        return EmergencyContactResponse(
            id=contact.id,
            name=contact.name,
            phone=contact.phone,
            location_id=contact.location_id,
            is_default=contact.is_default,
            created_by=contact.created_by,
            created_at=contact.created_at,
        )

    async def create_emergency_contact(
        self,
        user_id: int,
        payload: EmergencyContactCreateRequest
    ):
        """
        Create a new emergency contact.
        Applies consistency rules and authorization checks.
        """

        user = self.user_service.get_user_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        if payload.is_default:
            if user.role != UserRole.SUPERADMIN:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only SUPERADMIN can create default emergency contacts.",
                )
            if payload.location_id is not None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Default emergency contacts cannot be associated with a location.",
                )

        # Create the emergency contact
        new_contact = EmergencyContact(
            name=payload.name,
            phone=payload.phone,
            location_id=payload.location_id,
            is_default=payload.is_default,
            created_by=user_id,
        )

        self.session.add(new_contact)
        await self.session.commit()
        await self.session.refresh(new_contact)

    async def update_emergency_contact(
        self,
        user_id: int,
        contact_id: int,
        payload: EmergencyContactUpdateRequest,
    ):
        """
        Update an existing emergency contact.
        Applies consistency rules and authorization checks.
        """
        user = self.user_service.get_user_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        contact = await self.get_emergency_contact_by_id(contact_id)

        if not contact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Emergency contact with id {contact_id} not found.",
            )

        if contact.is_default and user.role != UserRole.SUPERADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only SUPERADMIN can modify default emergency contacts.",
            )

        contact_model = payload.model_dump(exclude_none=True)
        for key, value in contact_model.items():
            setattr(contact, key, value)

        await self.session.commit()
        await self.session.refresh(contact)

    async def delete_emergency_contact(
        self,
        user_id: int,
        contact_id: int,
    ) -> None:
        """
        Delete an emergency contact.
        Only SUPERADMIN can delete default numbers.
        """
        contact = await self.get_emergency_contact_by_id(contact_id)

        if not contact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Emergency contact with id {contact_id} not found.",
            )

        user = self.user_service.get_user_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        if contact.is_default and user.role != UserRole.SUPERADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only SUPERADMIN can delete default emergency contacts.",
            )

        await self.session.delete(contact)
        await self.session.commit()


__all__ = ["EmergencyContactService"]
