"""Location service module for the Sentinel Enterprise API."""

# pylint: disable=no-member, singleton-comparison

from datetime import datetime
from typing import List, Optional, cast

from fastapi import HTTPException, status
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from src.core.enums import UserRole
from src.models import (
    Location,
    Company,
    CompanyStaff,
    UserLocationAccess,
    CompanyLocationAccess,
)
from src.schemas import (
    LocationCreateRequest,
    LocationUpdateRequest,
    LocationAssignCompanyRequest,
    LocationAssignUserRequest,
    LocationResponse,
)
from src.services.user_service import UserService
from src.services.company_service import CompanyService


class LocationService:
    """Service for location operations and soft delete."""

    def __init__(
        self,
        session: AsyncSession,
        user_service: Optional[UserService] = None,
        company_service: Optional[CompanyService] = None,
    ):
        self.session = session
        self.user_service = user_service or UserService(session)
        self.company_service = company_service or CompanyService(session)

    async def _get_location_by_id(
        self,
        location_id: int,
    ) -> Optional[LocationResponse]:
        stmt = select(Location).where(Location.id == location_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_location_by_id(self, location_id: int) -> Optional[LocationResponse]:
        """Public helper to retrieve a Location by ID (used by other services)."""
        return await self._get_location_by_id(location_id)

    async def list_locations(
        self,
        user_id: int,
        params: Params,
        company_id: Optional[int],
        search: Optional[str],
    ) -> Page[LocationResponse]:
        """List locations with optional filters."""
        user = await self.user_service.get_user_by_id(user_id)
        if not user or not getattr(user, "is_active", True):
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

            # Forced company_id if user is not superadmin and provided company_id
            company_id = my_company_id

        stmt = select(Location).where(Location.is_active == True).options(selectinload(Location.company_locations_accesses))  # noqa: E712

        if company_id is not None:
            stmt = stmt.join(
                CompanyLocationAccess,
                CompanyLocationAccess.location_id == Location.id,
            ).where(CompanyLocationAccess.company_id == company_id)

        if search:
            like_pattern = f"%{search}%"
            stmt = stmt.where(
                (Location.name.ilike(like_pattern))
                | (Location.address.ilike(like_pattern)),
            )

        return await paginate(
            self.session,
            stmt,
            params,
            transformer=lambda items: [
                LocationResponse(
                    id=location.id,
                    name=location.name,
                    address=location.address,
                    country=location.country,
                    logo=location.logo,
                    company_ids=[
                        access.company_id for access in location.company_locations_accesses
                    ],
                    is_active=location.is_active,
                    created_by=location.created_by,
                    created_at=location.created_at,
                )
                for location in cast(List[Location], items)
            ],
        )

    async def get_location_detail(
        self,
        user_id: int,
        location_id: int,
    ) -> Location:
        """Get a single location by ID."""

        location = await self.check_user_permission_on_location(user_id=user_id, location_id=location_id)

        return location

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

        update_data = payload.model_dump(exclude_none=True)
        for key, value in update_data.items():
            setattr(location, key, value)

        self.session.add(location)
        await self.session.commit()
        await self.session.refresh(location)
        return location

    async def soft_delete_location(
        self,
        location_id: int,
    ):
        """Soft delete a location by setting is_active = False."""
        location = await self._get_location_by_id(location_id)
        if not location or not location.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Location not found.",
            )

        location.is_active = False
        self.session.add(location)
        await self.session.commit()

    async def assign_company_to_location(
        self,
        requester_id: int,
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

        assignment = CompanyLocationAccess(
            company_id=payload.company_id,
            location_id=location_id,
            created_by=requester_id,
            created_at=datetime.now(),
        )

        self.session.add(assignment)
        await self.session.commit()
        return location

    async def assign_user_to_location(
        self,
        requester_id: int,
        location_id: int,
        payload: LocationAssignUserRequest,
    ):
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

        assignment_stmt = select(UserLocationAccess).where(
            UserLocationAccess.user_id == payload.user_id,
            UserLocationAccess.location_id == location_id,
        )
        assignment_result = await self.session.execute(assignment_stmt)
        existing_assignment = assignment_result.scalars().first()

        if existing_assignment:
            return

        assignment = UserLocationAccess(
            user_id=payload.user_id,
            location_id=location_id,
            created_by=requester_id,
            created_at=datetime.now(),
        )

        self.session.add(assignment)
        await self.session.commit()

    async def check_user_permission_on_location(
        self,
        user_id: int,
        location_id: int,
    ) -> Location:
        """Validate User-Company permission on location"""
        user = await self.user_service.get_user_by_id(user_id)
        if not user or not getattr(user, "is_active", True):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        is_superadmin = user.role == UserRole.SUPERADMIN

        location = await self.session.get(Location, location_id)
        if not location or not location.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Location not found.",
            )

        if is_superadmin:
            return location

        user_company_id = await self.company_service.get_company_id_by_user_id(user_id)
        if not user_company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no company assigned.",
            )

        company_location_stmt = select(CompanyLocationAccess).where(
            CompanyLocationAccess.location_id == location_id,
            CompanyLocationAccess.company_id == user_company_id,
        )
        company_location_result = await self.session.execute(company_location_stmt)
        company_location = company_location_result.scalars().first()

        if company_location is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not allowed for this location.",
            )

        return location
