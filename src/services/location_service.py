"""Location service module for the Sentinel Enterprise API."""

from __future__ import annotations

# pylint: disable=no-member, singleton-comparison

from datetime import datetime
from typing import List, Optional, cast

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.core.enums import UserRole
from src.models import (
    Location,
    Company,
    CompanyStaff,
    UserLocationAccess,
)
from src.schemas import (
    LocationCreateRequest,
    LocationUpdateRequest,
    LocationAssignCompanyRequest,
    LocationAssignUserRequest,
)
from src.services.user_service import UserService

COMPANY_SCOPED_ROLES: set[UserRole] = {
    UserRole.ADMIN,
    UserRole.SUBADMIN,
    UserRole.CLIENT,
}


class LocationService:
    """Service for location (portería) operations with RBAC and soft delete."""

    def __init__(
        self,
        session: AsyncSession,
        user_service: Optional[UserService] = None,
    ) -> None:
        self.session = session
        self.user_service = user_service or UserService(session)

    async def _get_location_by_id(self, location_id: int) -> Optional[Location]:
        stmt = select(Location).where(Location.id == location_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def _get_user_company_ids(self, user_id: int) -> List[int]:
        stmt = select(CompanyStaff.company_id).where(
            CompanyStaff.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        rows = result.all()
        return [row[0] for row in rows]

    async def _ensure_location_in_user_companies(
        self,
        location: Location,
        user_id: int,
    ) -> None:
        """Ensure the location belongs to one of the user's companies."""
        if location.company_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Location is not assigned to any company.",
            )

        company_ids = await self._get_user_company_ids(user_id)
        if location.company_id not in company_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to access this location.",
            )

    async def _ensure_user_assigned_to_location(
        self,
        location_id: int,
        user_id: int,
    ) -> None:
        """Ensure the janitor is assigned to the given location."""
        stmt = select(UserLocationAccess).where(
            UserLocationAccess.user_id == user_id,
            UserLocationAccess.location_id == location_id,
        )
        result = await self.session.execute(stmt)
        link = result.scalars().first()

        if not link:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to access this location.",
            )

    async def list_locations(
        self,
        user_id: int,
        role: UserRole,
        company_id: Optional[int],
        search: Optional[str],
    ) -> List[Location]:
        """List locations visible for the current user with RBAC."""
        stmt = select(Location).where(Location.is_active == True)  # noqa: E712

        if search:
            like_pattern = f"%{search}%"
            stmt = stmt.where(
                (Location.name.ilike(like_pattern))
                | (Location.address.ilike(like_pattern)),
            )

        if role is UserRole.SUPERADMIN:
            if company_id is not None:
                stmt = stmt.where(Location.company_id == company_id)

        elif role in COMPANY_SCOPED_ROLES:
            user_company_ids = await self._get_user_company_ids(user_id)
            if not user_company_ids:
                return []

            if company_id is not None:
                if company_id not in user_company_ids:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="You are not allowed to view locations for this company.",
                    )
                stmt = stmt.where(Location.company_id == company_id)
            else:
                stmt = stmt.where(Location.company_id.in_(user_company_ids))

        elif role is UserRole.JANITOR:
            stmt = (
                select(Location)
                .join(
                    UserLocationAccess,
                    UserLocationAccess.location_id == Location.id,
                )
                .where(
                    Location.is_active == True,  # noqa: E712
                    UserLocationAccess.user_id == user_id,
                )
            )

            if search:
                like_pattern = f"%{search}%"
                stmt = stmt.where(
                    (Location.name.ilike(like_pattern))
                    | (Location.address.ilike(like_pattern)),
                )

            if company_id is not None:
                stmt = stmt.where(Location.company_id == company_id)

        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to list locations.",
            )

        result = await self.session.execute(stmt)
        locations = result.scalars().all()
        return cast(List[Location], locations)

    async def get_location_detail(
        self,
        user_id: int,
        role: UserRole,
        location_id: int,
    ) -> Location:
        """Get a single location detail applying RBAC for visibility."""
        location = await self._get_location_by_id(location_id)
        if not location or not location.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Location not found.",
            )

        if role is UserRole.SUPERADMIN:
            return location

        if role in COMPANY_SCOPED_ROLES:
            await self._ensure_location_in_user_companies(location, user_id)
            return location

        if role is UserRole.JANITOR:
            await self._ensure_user_assigned_to_location(
                location_id=location_id,
                user_id=user_id,
            )
            return location

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to view this location.",
        )

    async def create_location(
        self,
        user_id: int,
        payload: LocationCreateRequest,
    ) -> Location:
        """Create a new location."""
        location = Location(
            name=payload.name,
            address=payload.address,
            country=payload.country,
            logo=payload.logo,
            company_id=None,
            is_active=True,
            created_by=user_id,
            created_at=datetime.now(),
        )

        self.session.add(location)
        await self.session.commit()
        await self.session.refresh(location)
        return location

    async def update_location(
        self,
        user_id: int,
        role: UserRole,
        location_id: int,
        payload: LocationUpdateRequest,
    ) -> Location:
        """Update an existing location."""
        location = await self._get_location_by_id(location_id)
        if not location or not location.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Location not found.",
            )

        if role in {UserRole.ADMIN, UserRole.SUBADMIN}:
            await self._ensure_location_in_user_companies(location, user_id)

        update_data = payload.model_dump(exclude_none=True)
        for key, value in update_data.items():
            setattr(location, key, value)

        self.session.add(location)
        await self.session.commit()
        await self.session.refresh(location)
        return location

    async def soft_delete_location(
        self,
        user_id: int,
        role: UserRole,
        location_id: int,
    ) -> None:
        """Soft delete a location by setting is_active = False."""
        location = await self._get_location_by_id(location_id)
        if not location or not location.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Location not found.",
            )

        if role is UserRole.ADMIN:
            await self._ensure_location_in_user_companies(location, user_id)

        location.is_active = False
        self.session.add(location)
        await self.session.commit()

    async def assign_company_to_location(
        self,
        user_id: int,
        role: UserRole,
        location_id: int,
        payload: LocationAssignCompanyRequest,
    ) -> Location:
        """Assign a company to a location."""
        location = await self._get_location_by_id(location_id)
        if not location or not location.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Location not found.",
            )

        company = await self.session.get(Company, payload.company_id)
        if not company or not company.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found.",
            )

        if role is UserRole.ADMIN:
            user_company_ids = await self._get_user_company_ids(user_id)
            if payload.company_id not in user_company_ids:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not allowed to assign this company to the location.",
                )

        location.company_id = payload.company_id
        self.session.add(location)
        await self.session.commit()
        await self.session.refresh(location)
        return location

    async def assign_user_to_location(
        self,
        requester_id: int,
        requester_role: UserRole,
        location_id: int,
        payload: LocationAssignUserRequest,
    ) -> UserLocationAccess:
        """Assign a janitor user to a location."""
        location = await self._get_location_by_id(location_id)
        if not location or not location.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Location not found.",
            )

        if location.company_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Location must be assigned to a company before adding users.",
            )

        if requester_role in {UserRole.ADMIN, UserRole.SUBADMIN}:
            await self._ensure_location_in_user_companies(
                location,
                requester_id,
            )

        target_user = await self.user_service.get_user_by_id(payload.user_id)
        if not target_user or not target_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        if target_user.role is not UserRole.JANITOR:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only janitors can be assigned to locations.",
            )

        staff_stmt = select(CompanyStaff).where(
            CompanyStaff.user_id == payload.user_id,
            CompanyStaff.company_id == location.company_id,
        )
        staff_result = await self.session.execute(staff_stmt)
        staff_link = staff_result.scalars().first()

        if not staff_link:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not linked to the location's company.",
            )

        link_stmt = select(UserLocationAccess).where(
            UserLocationAccess.user_id == payload.user_id,
            UserLocationAccess.location_id == location_id,
        )
        link_result = await self.session.execute(link_stmt)
        existing_link = link_result.scalars().first()

        if existing_link:
            return existing_link

        new_link = UserLocationAccess(
            user_id=payload.user_id,
            location_id=location_id,
            created_by=requester_id,
            created_at=datetime.now(),
        )

        self.session.add(new_link)
        await self.session.commit()
        await self.session.refresh(new_link)
        return new_link
