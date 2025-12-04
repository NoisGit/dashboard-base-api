"""Location service module for the Sentinel Enterprise API."""

from __future__ import annotations

# pylint: disable=no-member, singleton-comparison

from datetime import datetime
from typing import Any, Dict, List, Optional, cast

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.core.enums import UserRole
from src.models import (
    Location,
    CompanyStaff,
    UserLocationAccess,
)
from src.schemas import (
    LocationCreateRequest,
    LocationUpdateRequest,
)

# Role constants derived from the global enum (single source of truth)
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

    # ---------- Auth / RBAC helpers ----------

    def _get_role(self, current_user: Dict[str, Any]) -> str:
        """Extract the role from the current user payload."""
        role = current_user.get("role")
        if role is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Role not found in token payload.",
            )
        return role

    def _get_user_id(self, current_user: Dict[str, Any]) -> int:
        """Extract the user_id from the current user payload."""
        user_id = current_user.get("user_id")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="user_id not found in token payload.",
            )
        return int(user_id)

    def _ensure_authenticated(self, current_user: Dict[str, Any]) -> None:
        """Ensure that the current user is authenticated."""
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required.",
            )

    def _ensure_can_create_locations(self, current_user: Dict[str, Any]) -> None:
        """
        Only SUPERADMIN and ADMIN can create locations.

        SUBADMIN, JANITOR and CLIENT cannot create locations.
        """
        role = self._get_role(current_user)
        if role not in {ROLE_SUPERADMIN, ROLE_ADMIN}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to create locations.",
            )

    def _ensure_can_update_locations(self, current_user: Dict[str, Any]) -> None:
        """
        SUPERADMIN, ADMIN and SUBADMIN can update locations.

        JANITOR and CLIENT cannot update locations.
        """
        role = self._get_role(current_user)
        if role not in {ROLE_SUPERADMIN, ROLE_ADMIN, ROLE_SUBADMIN}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to update locations.",
            )

    def _ensure_can_delete_locations(self, current_user: Dict[str, Any]) -> None:
        """
        Only SUPERADMIN and ADMIN can delete (soft delete) locations.
        """
        role = self._get_role(current_user)
        if role not in {ROLE_SUPERADMIN, ROLE_ADMIN}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to delete locations.",
            )

    # ---------- Helper queries ----------

    async def _get_location_by_id(self, location_id: int) -> Optional[Location]:
        """Return a location by ID (without RBAC)."""
        stmt = select(Location).where(Location.id == location_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def _get_user_company_ids(self, user_id: int) -> List[int]:
        """Return all company_ids associated to the user via CompanyStaff."""
        stmt = select(CompanyStaff.company_id).where(
            CompanyStaff.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        rows = result.all()
        return [row[0] for row in rows]

    async def _get_user_location_ids(self, user_id: int) -> List[int]:
        """Return all location_ids assigned to the user via UserLocationAccess."""
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
        """
        Ensure that the given location belongs to one of the user's companies.

        Used for ADMIN / SUBADMIN / CLIENT flows.
        """
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
        """
        Ensure that the user is explicitly assigned to the location via UserLocationAccess.

        Used mainly for JANITOR (portero) visibility.
        """
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

    # ---------- Public methods (used from router) ----------

    async def list_locations(
        self,
        current_user: Dict[str, Any],
        company_id: Optional[int],
        search: Optional[str],
        page: int,
        page_size: int,
    ) -> List[Location]:
        """
        List active locations visible for the current user.

        RBAC rules:
        - SUPERADMIN: sees all active locations (optionally filtered by company_id).
        - ADMIN / SUBADMIN / CLIENT: sees active locations of their companies.
        - JANITOR: sees only locations assigned via UserLocationAccess.
        """
        self._ensure_authenticated(current_user)

        role = self._get_role(current_user)
        user_id = self._get_user_id(current_user)

        # Base query: only active locations
        stmt = select(Location).where(Location.is_active == True)  # noqa: E712

        # Optional text search on name/address
        if search:
            like_pattern = f"%{search}%"
            stmt = stmt.where(
                (Location.name.ilike(like_pattern))
                | (Location.address.ilike(like_pattern))
            )

        if role == ROLE_SUPERADMIN:
            # Full visibility, optional company filter
            if company_id is not None:
                stmt = stmt.where(Location.company_id == company_id)

        elif role in COMPANY_SCOPED_ROLES:
            # Filter by user's companies
            user_company_ids = await self._get_user_company_ids(user_id)
            if not user_company_ids:
                # User has no companies -> no locations
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

        elif role == ROLE_JANITOR:
            # Porteros: only locations they are assigned to
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
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to list locations.",
            )

        # Pagination
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
        """
        Return a single active location, applying RBAC:

        - SUPERADMIN: can view any active location.
        - ADMIN / SUBADMIN / CLIENT: can view locations of their companies.
        - JANITOR: can view locations they are assigned to.
        """
        self._ensure_authenticated(current_user)

        role = self._get_role(current_user)
        user_id = self._get_user_id(current_user)

        location = await self._get_location_by_id(location_id)
        if not location or not location.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
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
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to view this location.",
        )

    async def create_location(
        self,
        current_user: Dict[str, Any],
        payload: LocationCreateRequest,
    ) -> Location:
        """
        Create a new location (portería).

        Rules:
        - Only SUPERADMIN and ADMIN can create locations.
        - Locations are created as active and without company_id.
          (Company assignment is handled in task #26 via a specific endpoint.)
        """
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
        """
        Update an existing location.

        Rules:
        - SUPERADMIN: can update any active location.
        - ADMIN / SUBADMIN: can update locations of their companies.
        - JANITOR / CLIENT: cannot update locations.
        """
        self._ensure_authenticated(current_user)
        self._ensure_can_update_locations(current_user)

        role = self._get_role(current_user)
        user_id = self._get_user_id(current_user)

        location = await self._get_location_by_id(location_id)
        if not location or not location.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Location not found.",
            )

        if role in {ROLE_ADMIN, ROLE_SUBADMIN}:
            await self._ensure_location_in_user_companies(location, user_id)

        # SUPERADMIN passes without additional checks

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
        """
        Soft delete a location by setting is_active = False.

        Rules:
        - Only SUPERADMIN and ADMIN can delete locations.
        - ADMIN can delete only locations of their companies.
        """
        self._ensure_authenticated(current_user)
        self._ensure_can_delete_locations(current_user)

        role = self._get_role(current_user)
        user_id = self._get_user_id(current_user)

        location = await self._get_location_by_id(location_id)
        if not location or not location.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Location not found.",
            )

        if role == ROLE_ADMIN:
            await self._ensure_location_in_user_companies(location, user_id)

        location.is_active = False
        self.session.add(location)
        await self.session.commit()
