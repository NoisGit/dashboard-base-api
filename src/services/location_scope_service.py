"""Centralized location scope helpers for Coredeck API."""

from typing import Optional

from fastapi import HTTPException, status
from sqlmodel import select

from src.core.enums import UserRole
from src.models import CompanyLocationAccess
from src.services.location_service import LocationService


class LocationScopeService(LocationService):
    """Location service with centralized company and location scope checks."""

    async def get_company_id_for_user(
        self,
        user_id: int,
        company_id: Optional[int] = None,
    ) -> int:
        """Resolve company scope for a user."""
        user = await self.user_service.get_user_by_id(user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        if user.role == UserRole.SUPERADMIN:
            if company_id is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="company_id is required.",
                )
            return company_id

        my_company_id = await self.company_service.get_company_id_by_user_id(user_id)
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

    async def validate_location_for_company(
        self,
        user_id: int,
        company_id: int,
        location_id: Optional[int],
    ) -> None:
        """Validate location access and company ownership."""
        if location_id is None:
            return

        await self.check_user_permission_on_location(
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

    async def resolve_company_scope_for_location(
        self,
        user_id: int,
        company_id: Optional[int] = None,
        location_id: Optional[int] = None,
    ) -> int:
        """Resolve company scope and validate location access."""
        if company_id is not None:
            resolved_company_id = await self.get_company_id_for_user(
                user_id=user_id,
                company_id=company_id,
            )
            await self.validate_location_for_company(
                user_id=user_id,
                company_id=resolved_company_id,
                location_id=location_id,
            )
            return resolved_company_id

        if location_id is None:
            return await self.get_company_id_for_user(
                user_id=user_id,
                company_id=company_id,
            )

        await self.check_user_permission_on_location(
            user_id=user_id,
            location_id=location_id,
        )

        user = await self.user_service.get_user_by_id(user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        if user.role != UserRole.SUPERADMIN:
            my_company_id = await self.company_service.get_company_id_by_user_id(user_id)
            if not my_company_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User has no company assigned.",
                )
            return my_company_id

        stmt = select(CompanyLocationAccess.company_id).where(
            CompanyLocationAccess.location_id == location_id,
        )
        result = await self.session.execute(stmt)
        company_ids = list({row[0] for row in result.all()})

        if not company_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Location must be assigned to a company.",
            )

        if len(company_ids) > 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="company_id is required when location has multiple companies.",
            )

        return company_ids[0]


__all__ = ["LocationScopeService"]
