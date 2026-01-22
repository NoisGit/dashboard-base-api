"""Blacklist service module for the Sentinel Enterprise API."""

# pylint: disable=no-member, singleton-comparison

from typing import List, Optional, cast

from fastapi import HTTPException, status
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import desc, or_, select

from src.core.enums import UserRole
from src.models import (
    AccessList,
    ExternalPeople,
    Location,
    TypeAccessList,
)
from src.schemas import (
    BlacklistCreateRequest,
    BlacklistResponse,
)
from src.services.user_service import UserService
from src.services.location_service import LocationService


class BlacklistService:
    """Service for blacklist operations."""

    def __init__(
        self,
        session: AsyncSession,
        user_service: UserService,
        location_service: LocationService,
    ) -> None:
        self.session = session
        self.user_service = user_service
        self.location_service = location_service

    async def _get_blacklist_type(self, created_by: int) -> TypeAccessList:
        """Get or create blacklist type"""
        stmt = select(TypeAccessList).where(TypeAccessList.name == "blacklist")
        result = await self.session.execute(stmt)
        type_access = result.scalars().first()

        if type_access:
            return type_access

        type_access = TypeAccessList(
            name="blacklist",
            created_by=created_by,
        )

        self.session.add(type_access)
        await self.session.commit()
        await self.session.refresh(type_access)
        return type_access

    async def _get_external_by_id_number(
        self,
        id_number: str,
    ) -> Optional[ExternalPeople]:
        """Get external people by id_number."""
        stmt = select(ExternalPeople).where(
            ExternalPeople.id_number == id_number)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def _get_existing_blacklist_entry(
        self,
        location_id: int,
        type_access_list_id: int,
        id_number: str,
    ) -> Optional[AccessList]:
        """Get blacklist entry for location + id_number."""
        stmt = (
            select(AccessList)
            .join(
                ExternalPeople,
                ExternalPeople.id == AccessList.external_people_id,
            )
            .where(
                AccessList.location_id == location_id,
                AccessList.type_access_list_id == type_access_list_id,
                ExternalPeople.id_number == id_number,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def block_person(
        self,
        user_id: int,
        location_id: int,
        payload: BlacklistCreateRequest,
    ) -> BlacklistResponse:
        """Create or update blacklist entry."""
        await self.location_service.check_user_permission_on_location(
            user_id=user_id,
            location_id=location_id,
        )

        reason = (payload.reason or "").strip()
        if not reason:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reason is required.",
            )

        blacklist_type = await self._get_blacklist_type(created_by=user_id)

        existing = await self._get_existing_blacklist_entry(
            location_id=location_id,
            type_access_list_id=blacklist_type.id,
            id_number=payload.id_number,
        )

        external = await self._get_external_by_id_number(payload.id_number)
        if not external:
            external = ExternalPeople(
                name=payload.full_name,
                id_number=payload.id_number,
                created_by=user_id,
            )
            self.session.add(external)
            await self.session.commit()
            await self.session.refresh(external)
        else:
            if payload.full_name and external.name != payload.full_name:
                external.name = payload.full_name
                self.session.add(external)
                await self.session.commit()
                await self.session.refresh(external)

        if existing:
            existing.reason = reason
            existing.name = payload.full_name
            self.session.add(existing)
            await self.session.commit()
            await self.session.refresh(existing)

            return BlacklistResponse(
                id=existing.id,
                location_id=existing.location_id,
                id_number=external.id_number,
                full_name=existing.name,
                reason=existing.reason or "",
                created_at=existing.created_at,
            )

        entry = AccessList(
            location_id=location_id,
            external_people_id=external.id,
            type_access_list_id=blacklist_type.id,
            name=payload.full_name,
            reason=reason,
            vehicle_plate=None,
            expiration_date=None,
            file_name=None,
            created_by=user_id,
        )

        self.session.add(entry)
        await self.session.commit()
        await self.session.refresh(entry)

        return BlacklistResponse(
            id=entry.id,
            location_id=entry.location_id,
            id_number=external.id_number,
            full_name=entry.name,
            reason=entry.reason or "",
            created_at=entry.created_at,
        )

    async def list_blacklist(
        self,
        user_id: int,
        location_id: int,
        params: Params,
        search: Optional[str] = None,
    ) -> Page[BlacklistResponse]:
        """List blacklist by location."""
        await self.location_service.check_user_permission_on_location(
            user_id=user_id,
            location_id=location_id,
        )

        blacklist_type = await self._get_blacklist_type(created_by=user_id)

        stmt = (
            select(
                AccessList.id,
                AccessList.location_id,
                AccessList.name,
                AccessList.reason,
                AccessList.created_at,
                ExternalPeople.id_number,
            )
            .join(
                ExternalPeople,
                ExternalPeople.id == AccessList.external_people_id,
            )
            .where(
                AccessList.location_id == location_id,
                AccessList.type_access_list_id == blacklist_type.id,
            )
            .order_by(desc(AccessList.created_at))
        )

        if search:
            like_pattern = f"%{search}%"
            stmt = stmt.where(
                or_(
                    ExternalPeople.id_number.ilike(like_pattern),
                    ExternalPeople.name.ilike(like_pattern),
                    AccessList.name.ilike(like_pattern),
                )
            )

        return await paginate(
            self.session,
            stmt,
            params,
            transformer=lambda items: [
                BlacklistResponse(
                    id=item.id,
                    location_id=item.location_id,
                    id_number=item.id_number,
                    full_name=item.name,
                    reason=item.reason or "",
                    created_at=item.created_at,
                )
                for item in cast(List, items)
            ],
        )

    async def unblock_person(
        self,
        user_id: int,
        location_id: int,
        id_number: str,
    ) -> None:
        """Remove blacklist entry."""
        await self.location_service.check_user_permission_on_location(
            user_id=user_id,
            location_id=location_id,
        )

        blacklist_type = await self._get_blacklist_type(created_by=user_id)

        existing = await self._get_existing_blacklist_entry(
            location_id=location_id,
            type_access_list_id=blacklist_type.id,
            id_number=id_number,
        )

        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Blacklist entry not found.",
            )

        await self.session.delete(existing)
        await self.session.commit()
