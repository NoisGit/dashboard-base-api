"""Whitelist service module for the Sentinel Enterprise API."""

# pylint: disable=no-member, singleton-comparison

from datetime import date
from typing import List, Optional, cast

from fastapi import HTTPException, status
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import desc, or_, select

from src.core.enums import UserRole
from src.models import (
    AccessList,
    CompanyStaff,
    ExternalPeople,
    Location,
    TypeAccessList,
)
from src.schemas import (
    WhitelistCreateRequest,
    WhitelistResponse,
)
from src.services.user_service import UserService


class WhitelistService:
    """Service for whitelist operations."""

    def __init__(
        self,
        session: AsyncSession,
        user_service: UserService,
    ) -> None:
        self.session = session
        self.user_service = user_service

    async def _get_user_company_id(self, user_id: int) -> Optional[int]:
        """Get user's company id."""
        stmt = (
            select(CompanyStaff.company_id)
            .where(CompanyStaff.user_id == user_id)
            .order_by(desc(CompanyStaff.created_at))
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def _ensure_manage_permission(self, user_id: int):
        """Check manage permission."""
        user = await self.user_service.get_user_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        if user.role not in (
            UserRole.SUPERADMIN,
            UserRole.ADMIN,
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions.",
            )

        return user

    async def _ensure_location_access(
        self,
        user_id: int,
        location_id: int,
    ) -> Location:
        """Validate location."""
        user = await self._ensure_manage_permission(user_id)

        location = await self.session.get(Location, location_id)
        if not location or not location.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Location not found.",
            )

        if user.role == UserRole.SUPERADMIN:
            return location

        user_company_id = await self._get_user_company_id(user_id)
        if not user_company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no company assigned.",
            )

        if not location.company_id or location.company_id != user_company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not allowed for this location.",
            )

        return location

    async def _get_whitelist_type(self, created_by: int) -> TypeAccessList:
        """Get or create whitelist type."""
        stmt = select(TypeAccessList).where(TypeAccessList.name == "whitelist")
        result = await self.session.execute(stmt)
        type_access = result.scalars().first()

        if type_access:
            return type_access

        type_access = TypeAccessList(
            name="whitelist",
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

    async def _get_existing_whitelist_entry(
        self,
        location_id: int,
        type_access_list_id: int,
        id_number: str,
    ) -> Optional[AccessList]:
        """Get whitelist entry for location + id_number."""
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

    def _is_active(self, expiration_date: Optional[date]) -> bool:
        """Check active state by expiration date."""
        if expiration_date is None:
            return True
        return expiration_date >= date.today()

    async def allow_person(
        self,
        user_id: int,
        location_id: int,
        payload: WhitelistCreateRequest,
    ) -> WhitelistResponse:
        """Create whitelist entry."""
        await self._ensure_location_access(user_id, location_id)

        id_number = (payload.id_number or "").strip()
        full_name = (payload.full_name or "").strip()
        role = (payload.role or "").strip() or None

        if not id_number:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="id_number is required.",
            )

        if not full_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="full_name is required.",
            )

        if payload.expiration_date is not None and payload.expiration_date < date.today():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="expiration_date must be today or a future date.",
            )

        whitelist_type = await self._get_whitelist_type(created_by=user_id)

        existing = await self._get_existing_whitelist_entry(
            location_id=location_id,
            type_access_list_id=whitelist_type.id,
            id_number=id_number,
        )

        if existing and self._is_active(existing.expiration_date):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Whitelist entry already exists for this location.",
            )

        external = await self._get_external_by_id_number(id_number)
        if not external:
            external = ExternalPeople(
                name=full_name,
                id_number=id_number,
                created_by=user_id,
            )
            self.session.add(external)
            await self.session.commit()
            await self.session.refresh(external)
        else:
            if full_name and external.name != full_name:
                external.name = full_name
                self.session.add(external)
                await self.session.commit()
                await self.session.refresh(external)

        if existing and not self._is_active(existing.expiration_date):
            existing.external_people_id = external.id
            existing.name = full_name
            existing.reason = role
            existing.expiration_date = payload.expiration_date
            existing.created_by = user_id

            self.session.add(existing)
            await self.session.commit()
            await self.session.refresh(existing)

            return WhitelistResponse(
                id=existing.id,
                location_id=existing.location_id,
                id_number=external.id_number,
                full_name=existing.name,
                role=existing.reason,
                expiration_date=existing.expiration_date,
                created_at=existing.created_at,
            )

        entry = AccessList(
            location_id=location_id,
            external_people_id=external.id,
            type_access_list_id=whitelist_type.id,
            name=full_name,
            reason=role,
            vehicle_plate=None,
            expiration_date=payload.expiration_date,
            file_name=None,
            created_by=user_id,
        )

        self.session.add(entry)
        await self.session.commit()
        await self.session.refresh(entry)

        return WhitelistResponse(
            id=entry.id,
            location_id=entry.location_id,
            id_number=external.id_number,
            full_name=entry.name,
            role=entry.reason,
            expiration_date=entry.expiration_date,
            created_at=entry.created_at,
        )

    async def list_whitelist(
        self,
        user_id: int,
        location_id: int,
        params: Params,
        search: Optional[str] = None,
        only_valid: bool = True,
    ) -> Page[WhitelistResponse]:
        """List whitelist by location."""
        await self._ensure_location_access(user_id, location_id)

        whitelist_type = await self._get_whitelist_type(created_by=user_id)

        stmt = (
            select(
                AccessList.id,
                AccessList.location_id,
                AccessList.name,
                AccessList.reason,
                AccessList.expiration_date,
                AccessList.created_at,
                ExternalPeople.id_number,
            )
            .join(
                ExternalPeople,
                ExternalPeople.id == AccessList.external_people_id,
            )
            .where(
                AccessList.location_id == location_id,
                AccessList.type_access_list_id == whitelist_type.id,
            )
            .order_by(desc(AccessList.created_at))
        )

        if only_valid:
            today = date.today()
            stmt = stmt.where(
                or_(
                    AccessList.expiration_date == None,  # noqa: E711
                    AccessList.expiration_date >= today,
                )
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
                WhitelistResponse(
                    id=row.id,
                    location_id=row.location_id,
                    id_number=row.id_number,
                    full_name=row.name,
                    role=row.reason,
                    expiration_date=row.expiration_date,
                    created_at=row.created_at,
                )
                for row in cast(List, items)
            ],
        )

    async def revoke_person(
        self,
        user_id: int,
        location_id: int,
        id_number: str,
    ) -> None:
        """Revoke whitelist entry."""
        await self._ensure_location_access(user_id, location_id)

        whitelist_type = await self._get_whitelist_type(created_by=user_id)

        existing = await self._get_existing_whitelist_entry(
            location_id=location_id,
            type_access_list_id=whitelist_type.id,
            id_number=id_number,
        )

        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Whitelist entry not found.",
            )

        await self.session.delete(existing)
        await self.session.commit()
