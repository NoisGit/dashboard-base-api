"""Emergency contact service module for the Locentr API."""

from typing import List, Optional, cast

from fastapi import HTTPException, status
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlmodel import paginate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, or_, desc

from src.core.enums import UserRole
from src.models import EmergencyContact
from src.schemas import (
    EmergencyContactCreateRequest,
    EmergencyContactUpdateRequest,
    EmergencyContactResponse,
)
from src.services.location_service import LocationService
from src.services.user_service import UserService


class EmergencyContactService:
    """Service for emergency contact operations."""

    def __init__(
        self,
        session: AsyncSession,
        user_service: UserService,
        location_service: LocationService,
    ):
        self.session = session
        self.user_service = user_service
        self.location_service = location_service

    async def get_emergency_contact_by_id(
        self,
        contact_id: int,
    ) -> Optional[EmergencyContact]:
        """Get emergency contact by ID."""
        stmt = select(EmergencyContact).where(EmergencyContact.id == contact_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def _ensure_can_access_location(
        self,
        user_id: int,
        location_id: Optional[int],
    ) -> None:
        """Validate location access."""
        if location_id is None:
            return

        await self.location_service.check_user_permission_on_location(
            user_id=user_id,
            location_id=location_id,
        )

    async def list_emergency_contacts(
        self,
        user_id: int,
        location_id: int,
        params: Params,
    ) -> Page[EmergencyContactResponse]:
        """
        List emergency contacts for a location.
        Returns both default country numbers (is_default=TRUE)
        and location-specific numbers.
        """
        await self._ensure_can_access_location(user_id, location_id)

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
        user_id: int,
        contact_id: int,
    ) -> EmergencyContactResponse:
        """Get a single emergency contact by ID."""
        contact = await self.get_emergency_contact_by_id(contact_id)

        if not contact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Emergency contact with id {contact_id} not found.",
            )

        if not contact.is_default:
            await self._ensure_can_access_location(user_id, contact.location_id)

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
        """Create a new emergency contact."""
        user = await self.user_service.get_user_by_id(user_id)

        if not user or not user.is_active:
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
        else:
            await self._ensure_can_access_location(user_id, payload.location_id)

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
        """Update an existing emergency contact."""
        user = await self.user_service.get_user_by_id(user_id)

        if not user or not user.is_active:
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

        if not contact.is_default:
            await self._ensure_can_access_location(user_id, contact.location_id)

        contact_model = payload.model_dump(exclude_none=True)
        next_location_id = contact_model.get("location_id", contact.location_id)
        next_is_default = contact_model.get("is_default", contact.is_default)

        if next_is_default and next_location_id is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Default emergency contacts cannot be associated with a location.",
            )

        if not next_is_default:
            await self._ensure_can_access_location(user_id, next_location_id)

        for key, value in contact_model.items():
            setattr(contact, key, value)

        await self.session.commit()
        await self.session.refresh(contact)

    async def delete_emergency_contact(
        self,
        user_id: int,
        contact_id: int,
    ):
        """Delete an emergency contact."""
        contact = await self.get_emergency_contact_by_id(contact_id)

        if not contact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Emergency contact with id {contact_id} not found.",
            )

        user = await self.user_service.get_user_by_id(user_id)

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        if contact.is_default and user.role != UserRole.SUPERADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only SUPERADMIN can delete default emergency contacts.",
            )

        if not contact.is_default:
            await self._ensure_can_access_location(user_id, contact.location_id)

        await self.session.delete(contact)
        await self.session.commit()


__all__ = ["EmergencyContactService"]
