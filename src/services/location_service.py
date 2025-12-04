"""Location service module for the Sentinel Enterprise API."""

from __future__ import annotations

# pylint: disable=no-member, singleton-comparison

from datetime import datetime
from typing import Any, Dict, List, Optional, cast

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.core.enums import UserRole
from src.models import (
    Location,
    Company,
    CompanyStaff,
    User,
    UserLocationAccess,
)
from src.schemas import (
    LocationCreateRequest,
    LocationUpdateRequest,
    LocationAssignCompanyRequest,
    LocationAssignUserRequest,
)

ROLE_SUPERADMIN = UserRole.SUPERADMIN.value
ROLE_ADMIN = UserRole.ADMIN.value
ROLE_SUBADMIN = UserRole.SUBADMIN.value
ROLE_JANITOR = UserRole.JANITOR.value
ROLE_CLIENT = UserRole.CLIENT.value

ADMIN_LIKE_ROLES = {ROLE_ADMIN, ROLE_SUPERADMIN}
COMPANY_SCOPED_ROLES = {ROLE_ADMIN, ROLE_SUBADMIN, ROLE_CLIENT}


class LocationService:
    """Service for location (portería) operations with RBAC and soft delete."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ---------- RBAC helpers ----------

    def _get_role(self, current_user: Dict[str, Any]) -> str:
        role = current_user.get("role")
        if role is None:
            raise HTTPException(
                status_code=401,
                detail="Role not found in token payload.",
            )
        return role

    def _get_user_id(self, current_user: Dict[str, Any]) -> int:
        user_id = current_user.get("user_id")
        if user_id is None:
            raise HTTPException(
                status_code=401,
                detail="user_id not found in token payload.",
            )
        return int(user_id)

    def _ensure_authenticated(self, current_user: Dict[str, Any]) -> None:
        if not current_user:
            raise HTTPException(
                status_code=401,
                detail="Authentication required.",
            )

    def _ensure_can_create_locations(self, current_user: Dict[str, Any]) -> None:
        role = self._get_role(current_user)
        if role not in {ROLE_SUPERADMIN, ROLE_ADMIN}:
            raise HTTPException(
                status_code=403,
                detail="You are not allowed to create locations.",
            )

    def _ensure_can_update_locations(self, current_user: Dict[str, Any]) -> None:
        role = self._get_role(current_user)
        if role not in {ROLE_SUPERADMIN, ROLE_ADMIN, ROLE_SUBADMIN}:
            raise HTTPException(
                status_code=403,
                detail="You are not allowed to update locations.",
            )

    def _ensure_can_delete_locations(self, current_user: Dict[str, Any]) -> None:
        role = self._get_role(current_user)
        if role not in {ROLE_SUPERADMIN, ROLE_ADMIN}:
            raise HTTPException(
                status_code=403,
                detail="You are not allowed to delete locations.",
            )

    # ---------- Helper queries ----------

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

    async def _get_user_location_ids(self, user_id: int) -> List[int]:
        stmt = select(UserLocationAccess.location_id).where(
            UserLocationAccess.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        rows = result.all()
        return [row[0] for row in rows]

    async def _ensure_location_in_user_companies(
        self,
        location: Location,
        user_id: int,
    ) -> None:
        if location.company_id is None:
            raise HTTPException(
                status_code=403,
                detail="Location is not assigned to any company.",
            )

        company_ids = await self._get_user_company_ids(user_id)
        if location.company_id not in company_ids:
            raise HTTPException(
                status_code=403,
                detail="You are not allowed to access this location.",
            )

    async def _ensure_user_assigned_to_location(
        self,
        location_id: int,
        user_id: int,
    ) -> None:
        stmt = select(UserLocationAccess).where(
            UserLocationAccess.user_id == user_id,
            UserLocationAccess.location_id == location_id,
        )
        result = await self.session.execute(stmt)
        link = result.scalars().first()

        if not link:
            raise HTTPException(
                status_code=403,
                detail="You are not allowed to access this location.",
            )

    # ---------- Public methods ----------

    async def list_locations(
        self,
        current_user: Dict[str, Any],
        company_id: Optional[int],
        search: Optional[str],
        page: int,
        page_size: int,
    ) -> List[Location]:
        """List locations visible for the current user with RBAC and paginación."""
        self._ensure_authenticated(current_user)

        role = self._get_role(current_user)
        user_id = self._get_user_id(current_user)

        stmt = select(Location).where(Location.is_active == True)  # noqa: E712

        if search:
            like_pattern = f"%{search}%"
            stmt = stmt.where(
                (Location.name.ilike(like_pattern))
                | (Location.address.ilike(like_pattern))
            )

        if role == ROLE_SUPERADMIN:
            if company_id is not None:
                stmt = stmt.where(Location.company_id == company_id)

        elif role in COMPANY_SCOPED_ROLES:
            user_company_ids = await self._get_user_company_ids(user_id)
            if not user_company_ids:
                return []

            if company_id is not None:
                if company_id not in user_company_ids:
                    raise HTTPException(
                        status_code=403,
                        detail="You are not allowed to view locations for this company.",
                    )
                stmt = stmt.where(Location.company_id == company_id)
            else:
                stmt = stmt.where(Location.company_id.in_(user_company_ids))

        elif role == ROLE_JANITOR:
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
                    | (Location.address.ilike(like_pattern))
                )

            if company_id is not None:
                stmt = stmt.where(Location.company_id == company_id)

        else:
            raise HTTPException(
                status_code=403,
                detail="You are not allowed to list locations.",
            )

        if page < 1:
            page = 1
        if page_size <= 0:
            page_size = 20

        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)

        result = await self.session.execute(stmt)
        locations = result.scalars().all()
        return cast(List[Location], locations)

    async def get_location_detail(
        self,
        current_user: Dict[str, Any],
        location_id: int,
    ) -> Location:
        """Get a single location detail applying RBAC for visibility."""
        self._ensure_authenticated(current_user)

        role = self._get_role(current_user)
        user_id = self._get_user_id(current_user)

        location = await self._get_location_by_id(location_id)
        if not location or not location.is_active:
            raise HTTPException(
                status_code=404,
                detail="Location not found.",
            )

        if role == ROLE_SUPERADMIN:
            return location

        if role in COMPANY_SCOPED_ROLES:
            await self._ensure_location_in_user_companies(location, user_id)
            return location

        if role == ROLE_JANITOR:
            await self._ensure_user_assigned_to_location(
                location_id=location_id,
                user_id=user_id,
            )
            return location

        raise HTTPException(
            status_code=403,
            detail="You are not allowed to view this location.",
        )

    async def create_location(
        self,
        current_user: Dict[str, Any],
        payload: LocationCreateRequest,
    ) -> Location:
        """Create a new location enforcing RBAC rules."""
        self._ensure_authenticated(current_user)
        self._ensure_can_create_locations(current_user)

        creator_id = self._get_user_id(current_user)

        location = Location(
            name=payload.name,
            address=payload.address,
            country=payload.country,
            logo=payload.logo,
            company_id=None,
            is_active=True,
            created_by=creator_id,
            created_at=datetime.now(),
        )

        self.session.add(location)
        await self.session.commit()
        await self.session.refresh(location)
        return location

    async def update_location(
        self,
        current_user: Dict[str, Any],
        location_id: int,
        payload: LocationUpdateRequest,
    ) -> Location:
        """Update an existing location enforcing RBAC rules."""
        self._ensure_authenticated(current_user)
        self._ensure_can_update_locations(current_user)

        role = self._get_role(current_user)
        user_id = self._get_user_id(current_user)

        location = await self._get_location_by_id(location_id)
        if not location or not location.is_active:
            raise HTTPException(
                status_code=404,
                detail="Location not found.",
            )

        if role in {ROLE_ADMIN, ROLE_SUBADMIN}:
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
        current_user: Dict[str, Any],
        location_id: int,
    ) -> None:
        """Soft delete a location by setting is_active to False."""
        self._ensure_authenticated(current_user)
        self._ensure_can_delete_locations(current_user)

        role = self._get_role(current_user)
        user_id = self._get_user_id(current_user)

        location = await self._get_location_by_id(location_id)
        if not location or not location.is_active:
            raise HTTPException(
                status_code=404,
                detail="Location not found.",
            )

        if role == ROLE_ADMIN:
            await self._ensure_location_in_user_companies(location, user_id)

        location.is_active = False
        self.session.add(location)
        await self.session.commit()

    async def assign_company_to_location(
        self,
        current_user: Dict[str, Any],
        location_id: int,
        payload: LocationAssignCompanyRequest,
    ) -> Location:
        """Assign a company to a location with RBAC checks."""
        self._ensure_authenticated(current_user)

        role = self._get_role(current_user)
        user_id = self._get_user_id(current_user)

        if role not in {ROLE_SUPERADMIN, ROLE_ADMIN}:
            raise HTTPException(
                status_code=403,
                detail="You are not allowed to assign company to locations.",
            )

        location = await self._get_location_by_id(location_id)
        if not location or not location.is_active:
            raise HTTPException(
                status_code=404,
                detail="Location not found.",
            )

        company = await self.session.get(Company, payload.company_id)
        if not company or not company.is_active:
            raise HTTPException(
                status_code=404,
                detail="Company not found.",
            )

        if role == ROLE_ADMIN:
            user_company_ids = await self._get_user_company_ids(user_id)
            if payload.company_id not in user_company_ids:
                raise HTTPException(
                    status_code=403,
                    detail="You are not allowed to assign this company to the location.",
                )

        location.company_id = payload.company_id
        self.session.add(location)
        await self.session.commit()
        await self.session.refresh(location)
        return location

    async def assign_user_to_location(
        self,
        current_user: Dict[str, Any],
        location_id: int,
        payload: LocationAssignUserRequest,
    ) -> UserLocationAccess:
        """Assign a janitor user to a location, validating company and role."""
        self._ensure_authenticated(current_user)

        role = self._get_role(current_user)
        actor_id = self._get_user_id(current_user)

        if role not in {ROLE_SUPERADMIN, ROLE_ADMIN, ROLE_SUBADMIN}:
            raise HTTPException(
                status_code=403,
                detail="You are not allowed to assign users to locations.",
            )

        location = await self._get_location_by_id(location_id)
        if not location or not location.is_active:
            raise HTTPException(
                status_code=404,
                detail="Location not found.",
            )

        if location.company_id is None:
            raise HTTPException(
                status_code=400,
                detail="Location must be assigned to a company before adding users.",
            )

        if role in {ROLE_ADMIN, ROLE_SUBADMIN}:
            await self._ensure_location_in_user_companies(location, actor_id)

        user_stmt = select(User).where(User.id == payload.user_id)
        user_result = await self.session.execute(user_stmt)
        target_user = user_result.scalars().first()

        if not target_user or not target_user.is_active:
            raise HTTPException(
                status_code=404,
                detail="User not found.",
            )

        if target_user.role != ROLE_JANITOR:
            raise HTTPException(
                status_code=400,
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
                status_code=400,
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
            created_by=actor_id,
            created_at=datetime.now(),
        )

        self.session.add(new_link)
        await self.session.commit()
        await self.session.refresh(new_link)
        return new_link
