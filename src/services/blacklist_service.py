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
    CompanyLocationAccess,
    ExternalPeople,
    TypeAccessList,
)
from src.schemas import (
    BlacklistCheckResponse,
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

    async def _get_whitelist_type_id(self) -> Optional[int]:
        stmt = select(TypeAccessList).where(TypeAccessList.name == "whitelist")
        result = await self.session.execute(stmt)
        type_access = result.scalars().first()
        return type_access.id if type_access else None

    async def _ensure_not_whitelisted(
        self,
        company_id: int,
        location_id: Optional[int],
        id_number: str,
    ) -> None:
        whitelist_type_id = await self._get_whitelist_type_id()
        if not whitelist_type_id:
            return

        stmt = (
            select(AccessList.id)
            .join(
                ExternalPeople,
                ExternalPeople.id == AccessList.external_people_id,
            )
            .where(
                AccessList.company_id == company_id,
                AccessList.type_access_list_id == whitelist_type_id,
                ExternalPeople.id_number == id_number,
            )
        )

        if location_id is None:
            pass
        else:
            stmt = stmt.where(
                or_(
                    AccessList.location_id == location_id,
                    AccessList.location_id == None,  # noqa: E711
                )
            )

        result = await self.session.execute(stmt)
        row = result.scalars().first()
        if row:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La persona ya está en lista blanca. Elimine el registro antes de crear lista negra.",
            )

    async def _get_external_by_id_number(
        self,
        id_number: str,
    ) -> Optional[ExternalPeople]:
        """Get external people by id_number."""
        stmt = select(ExternalPeople).where(
            ExternalPeople.id_number == id_number
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def _get_company_id(
        self,
        user_id: int,
        company_id: Optional[int],
    ) -> int:
        user = await self.user_service.get_user_by_id(user_id)
        if not user or not getattr(user, "is_active", True):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        if user.role == UserRole.SUPERADMIN:
            if not company_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="company_id is required.",
                )
            return company_id

        my_company_id = await self.location_service.company_service.get_company_id_by_user_id(
            user_id
        )
        if not my_company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no company assigned.",
            )

        if company_id is not None and company_id != my_company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not allowed for this company.",
            )

        return my_company_id

    async def _validate_location_for_company(
        self,
        user_id: int,
        company_id: int,
        location_id: Optional[int],
    ) -> None:
        if location_id is None:
            return

        await self.location_service.check_user_permission_on_location(
            user_id=user_id,
            location_id=location_id,
        )

        stmt = select(CompanyLocationAccess).where(
            CompanyLocationAccess.company_id == company_id,
            CompanyLocationAccess.location_id == location_id,
        )
        result = await self.session.execute(stmt)
        row = result.scalars().first()

        if not row:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="company_id does not match location_id.",
            )

    async def _get_existing_blacklist_entry(
        self,
        company_id: int,
        location_id: Optional[int],
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
                AccessList.company_id == company_id,
                AccessList.type_access_list_id == type_access_list_id,
                ExternalPeople.id_number == id_number,
            )
        )

        if location_id is None:
            stmt = stmt.where(AccessList.location_id == None)  # noqa: E711
        else:
            stmt = stmt.where(AccessList.location_id == location_id)

        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def block_person(
        self,
        user_id: int,
        location_id: Optional[int],
        company_id: Optional[int],
        payload: BlacklistCreateRequest,
    ) -> BlacklistResponse:
        """Create or update blacklist entry."""
        company_id = await self._get_company_id(
            user_id=user_id,
            company_id=company_id,
        )
        await self._validate_location_for_company(
            user_id=user_id,
            company_id=company_id,
            location_id=location_id,
        )

        reason = (payload.reason or "").strip()
        if not reason:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reason is required.",
            )

        await self._ensure_not_whitelisted(
            company_id=company_id,
            location_id=location_id,
            id_number=payload.id_number,
        )

        blacklist_type = await self._get_blacklist_type(created_by=user_id)

        existing = await self._get_existing_blacklist_entry(
            company_id=company_id,
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
                company_id=existing.company_id,
                location_id=existing.location_id,
                external_people_id=external.id,
                id_number=external.id_number,
                full_name=existing.name,
                reason=existing.reason or "",
                created_at=existing.created_at,
            )

        entry = AccessList(
            company_id=company_id,
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
            company_id=entry.company_id,
            location_id=entry.location_id,
            external_people_id=external.id,
            id_number=external.id_number,
            full_name=entry.name,
            reason=entry.reason or "",
            created_at=entry.created_at,
        )

    async def list_blacklist(
        self,
        user_id: int,
        location_id: Optional[int],
        company_id: Optional[int],
        params: Params,
        search: Optional[str] = None,
    ) -> Page[BlacklistResponse]:
        """List blacklist by location."""
        company_id = await self._get_company_id(
            user_id=user_id,
            company_id=company_id,
        )
        await self._validate_location_for_company(
            user_id=user_id,
            company_id=company_id,
            location_id=location_id,
        )

        blacklist_type = await self._get_blacklist_type(created_by=user_id)

        stmt = (
            select(
                AccessList.id,
                AccessList.company_id,
                AccessList.location_id,
                AccessList.name,
                AccessList.reason,
                AccessList.created_at,
                ExternalPeople.id_number,
                ExternalPeople.id.label("external_people_id"),
            )
            .join(
                ExternalPeople,
                ExternalPeople.id == AccessList.external_people_id,
            )
            .where(
                AccessList.company_id == company_id,
                AccessList.type_access_list_id == blacklist_type.id,
            )
            .order_by(desc(AccessList.created_at))
        )

        if location_id is None:
            stmt = stmt.where(AccessList.location_id == None)  # noqa: E711
        else:
            stmt = stmt.where(
                or_(
                    AccessList.location_id == location_id,
                    AccessList.location_id == None,  # noqa: E711
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
                BlacklistResponse(
                    id=item.id,
                    company_id=item.company_id,
                    location_id=item.location_id,
                    external_people_id=getattr(item, "external_people_id", None),
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
        location_id: Optional[int],
        company_id: Optional[int],
        id_number: str,
    ) -> None:
        """Remove blacklist entry."""
        company_id = await self._get_company_id(
            user_id=user_id,
            company_id=company_id,
        )
        await self._validate_location_for_company(
            user_id=user_id,
            company_id=company_id,
            location_id=location_id,
        )

        blacklist_type = await self._get_blacklist_type(created_by=user_id)

        existing = await self._get_existing_blacklist_entry(
            company_id=company_id,
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

    async def check_blacklist(
        self,
        user_id: int,
        location_id: int,
        id_number: str,
    ) -> BlacklistCheckResponse:
        """Check if a person is in blacklist."""
        company_id = await self._get_company_id(
            user_id=user_id,
            company_id=None,
        )
        await self._validate_location_for_company(
            user_id=user_id,
            company_id=company_id,
            location_id=location_id,
        )

        blacklist_type = await self._get_blacklist_type(created_by=user_id)

        entry = await self._get_existing_blacklist_entry(
            company_id=company_id,
            location_id=location_id,
            type_access_list_id=blacklist_type.id,
            id_number=id_number,
        )

        if not entry:
            entry = await self._get_existing_blacklist_entry(
                company_id=company_id,
                location_id=None,
                type_access_list_id=blacklist_type.id,
                id_number=id_number,
            )

        if not entry:
            external = await self._get_external_by_id_number(id_number)
            return BlacklistCheckResponse(
                company_id=company_id,
                location_id=location_id,
                external_people_id=external.id if external else None,
                id_number=id_number,
                full_name=external.name if external else None,
                status="ALLOWED",
                message="Acceso permitido.",
                reason=None,
            )

        return BlacklistCheckResponse(
            company_id=entry.company_id,
            location_id=location_id,
            external_people_id=entry.external_people_id,
            id_number=id_number,
            full_name=entry.name,
            status="DENIED",
            message="No tiene acceso permitido. Lista negra.",
            reason=entry.reason or None,
        )
