"""Whitelist service module for the Sentinel Enterprise API."""

# pylint: disable=no-member, singleton-comparison

from datetime import datetime
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
    WhitelistCheckResponse,
    WhitelistCreateRequest,
    WhitelistResponse,
)
from src.services.user_service import UserService
from src.services.location_service import LocationService


class WhitelistService:
    """Service for whitelist operations."""

    def __init__(
        self,
        session: AsyncSession,
        user_service: UserService,
        location_service: LocationService,
    ) -> None:
        self.session = session
        self.user_service = user_service
        self.location_service = location_service

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

    async def _get_existing_whitelist_entry(
        self,
        company_id: int,
        location_id: Optional[int],
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

    def _is_active(self, expiration_date: Optional[datetime]) -> bool:
        """Check active state by expiration date."""
        if expiration_date is None:
            return True

        exp = expiration_date.replace(tzinfo=None) if expiration_date.tzinfo else expiration_date
        return exp >= datetime.now()

    async def allow_person(
        self,
        user_id: int,
        location_id: Optional[int],
        company_id: Optional[int],
        payload: WhitelistCreateRequest,
    ) -> WhitelistResponse:
        """Create whitelist entry."""
        company_id = await self._get_company_id(
            user_id=user_id,
            company_id=company_id,
        )
        await self._validate_location_for_company(
            user_id=user_id,
            company_id=company_id,
            location_id=location_id,
        )

        id_number = (payload.id_number or "").strip()
        full_name = (payload.full_name or "").strip()
        reason = (getattr(payload, "reason", None) or "").strip() or None

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

        expiration_date = None
        if getattr(payload, "expiration_date", None) is not None:
            expiration_date = payload.expiration_date.replace(tzinfo=None)  # type: ignore[union-attr]
            if expiration_date < datetime.now():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="expiration_date must be today or a future date.",
                )

        whitelist_type = await self._get_whitelist_type(created_by=user_id)

        existing = await self._get_existing_whitelist_entry(
            company_id=company_id,
            location_id=location_id,
            type_access_list_id=whitelist_type.id,
            id_number=id_number,
        )

        if existing and self._is_active(existing.expiration_date):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Whitelist entry already exists.",
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
            existing.reason = reason
            existing.expiration_date = expiration_date
            existing.created_by = user_id

            self.session.add(existing)
            await self.session.commit()
            await self.session.refresh(existing)

            return WhitelistResponse(
                id=existing.id,
                company_id=existing.company_id,
                location_id=existing.location_id,
                external_people_id=external.id,
                id_number=external.id_number,
                full_name=existing.name,
                reason=existing.reason,
                expiration_date=existing.expiration_date,
                created_at=existing.created_at,
            )

        entry = AccessList(
            company_id=company_id,
            location_id=location_id,
            external_people_id=external.id,
            type_access_list_id=whitelist_type.id,
            name=full_name,
            reason=reason,
            vehicle_plate=None,
            expiration_date=expiration_date,
            file_name=None,
            created_by=user_id,
        )

        self.session.add(entry)
        await self.session.commit()
        await self.session.refresh(entry)

        return WhitelistResponse(
            id=entry.id,
            company_id=entry.company_id,
            location_id=entry.location_id,
            external_people_id=external.id,
            id_number=external.id_number,
            full_name=entry.name,
            reason=entry.reason,
            expiration_date=entry.expiration_date,
            created_at=entry.created_at,
        )

    async def list_whitelist(
        self,
        user_id: int,
        location_id: Optional[int],
        company_id: Optional[int],
        params: Params,
        search: Optional[str] = None,
        include_expired: bool = False,
    ) -> Page[WhitelistResponse]:
        """List whitelist entries."""
        company_id = await self._get_company_id(
            user_id=user_id,
            company_id=company_id,
        )
        await self._validate_location_for_company(
            user_id=user_id,
            company_id=company_id,
            location_id=location_id,
        )

        whitelist_type = await self._get_whitelist_type(created_by=user_id)

        stmt = (
            select(
                AccessList.id,
                AccessList.company_id,
                AccessList.location_id,
                AccessList.name,
                AccessList.reason,
                AccessList.expiration_date,
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
                AccessList.type_access_list_id == whitelist_type.id,
            )
            .order_by(desc(AccessList.created_at))
        )

        if location_id is None:
            stmt = stmt.where(AccessList.location_id == None)  # noqa: E711
        else:
            stmt = stmt.where(AccessList.location_id == location_id)

        if not include_expired:
            now = datetime.now()
            stmt = stmt.where(
                or_(
                    AccessList.expiration_date == None,  # noqa: E711
                    AccessList.expiration_date >= now,
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
                    id=item.id,
                    company_id=item.company_id,
                    location_id=item.location_id,
                    external_people_id=getattr(item, "external_people_id", None),
                    id_number=item.id_number,
                    full_name=item.name,
                    reason=item.reason,
                    expiration_date=item.expiration_date,
                    created_at=item.created_at,
                )
                for item in cast(List, items)
            ],
        )

    async def revoke_person(
        self,
        user_id: int,
        location_id: Optional[int],
        company_id: Optional[int],
        id_number: str,
    ) -> None:
        """Revoke whitelist entry."""
        company_id = await self._get_company_id(
            user_id=user_id,
            company_id=company_id,
        )
        await self._validate_location_for_company(
            user_id=user_id,
            company_id=company_id,
            location_id=location_id,
        )

        whitelist_type = await self._get_whitelist_type(created_by=user_id)

        existing = await self._get_existing_whitelist_entry(
            company_id=company_id,
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

    async def check_whitelist(
        self,
        user_id: int,
        location_id: int,
        id_number: str,
    ) -> WhitelistCheckResponse:
        """Check if a person is in whitelist."""
        company_id = await self._get_company_id(
            user_id=user_id,
            company_id=None,
        )
        await self._validate_location_for_company(
            user_id=user_id,
            company_id=company_id,
            location_id=location_id,
        )

        whitelist_type = await self._get_whitelist_type(created_by=user_id)

        entry = await self._get_existing_whitelist_entry(
            company_id=company_id,
            location_id=location_id,
            type_access_list_id=whitelist_type.id,
            id_number=id_number,
        )

        if not entry:
            entry = await self._get_existing_whitelist_entry(
                company_id=company_id,
                location_id=None,
                type_access_list_id=whitelist_type.id,
                id_number=id_number,
            )

        if not entry or not self._is_active(entry.expiration_date):
            external = await self._get_external_by_id_number(id_number)
            return WhitelistCheckResponse(
                company_id=company_id,
                location_id=location_id,
                external_people_id=external.id if external else None,
                id_number=id_number,
                full_name=external.name if external else None,
                status="NONE",
                message="Acceso permitido.",
                reason=None,
                expiration_date=None,
            )

        return WhitelistCheckResponse(
            company_id=entry.company_id,
            location_id=location_id,
            external_people_id=entry.external_people_id,
            id_number=id_number,
            full_name=entry.name,
            status="WHITELIST",
            message="Acceso permitido. Lista blanca.",
            reason=entry.reason or None,
            expiration_date=entry.expiration_date,
        )
