"""Location logbook service module for the Sentinel Enterprise API."""

# pylint: disable=no-member, singleton-comparison

from datetime import datetime, timedelta
from typing import List, Optional, cast

from fastapi import HTTPException, status
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select, desc

from src.auth import create_secret_token_urlsafe
from src.core.enums import UserRole
from src.models import (
    Location,
    CompanyStaff,
    UserLocationAccess,
    LocationLogbook,
    LocationLogbookSettings,
    PoliceAccessPermit,
)
from src.schemas import (
    LocationLogbookCreateRequest,
    LocationLogbookResponse,
    LocationLogbookSettingsUpdateRequest,
    LocationLogbookSettingsResponse,
    PoliceLinkResponse,
    PoliceViewResponse,
)
from src.services.azure_service import AzureService
from src.services.user_service import UserService


class LocationLogbookService:
    """Service for location logbook operations."""

    def __init__(
        self,
        session: AsyncSession,
        user_service: UserService,
        azure_service: AzureService,
    ):
        self.session = session
        self.user_service = user_service
        self.azure_service = azure_service

    async def _get_location_by_id(
        self,
        location_id: int,
    ) -> Optional[Location]:
        stmt = select(Location).where(Location.id == location_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def _get_settings_by_location_id(
        self,
        location_id: int,
    ) -> Optional[LocationLogbookSettings]:
        stmt = select(LocationLogbookSettings).where(
            LocationLogbookSettings.location_id == location_id
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def _assert_location_exists(
        self,
        location_id: int,
    ) -> Location:
        location = await self._get_location_by_id(location_id)
        if not location or not location.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Location not found.",
            )
        return location

    async def _assert_user_can_access_location(
        self,
        user_id: int,
        location: Location,
    ):
        user = await self.user_service.get_user_by_id(user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        if user.role == UserRole.SUPERADMIN:
            return

        if location.company_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Location is not assigned to a company.",
            )

        if user.role in (UserRole.ADMIN, UserRole.SUBADMIN, UserRole.CLIENT):
            stmt = select(CompanyStaff).where(
                CompanyStaff.user_id == user_id,
                CompanyStaff.company_id == location.company_id,
            )
            result = await self.session.execute(stmt)
            staff_link = result.scalars().first()

            if not staff_link:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User has no access to this location.",
                )
            return

        if user.role is UserRole.JANITOR:
            stmt = select(UserLocationAccess).where(
                UserLocationAccess.user_id == user_id,
                UserLocationAccess.location_id == location.id,
            )
            result = await self.session.execute(stmt)
            assignment = result.scalars().first()

            if not assignment:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User has no access to this location.",
                )
            return

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User has no access to this location.",
        )

    async def _assert_logbook_enabled(
        self,
        location_id: int,
    ):
        settings = await self._get_settings_by_location_id(location_id)
        if not settings or not settings.is_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Location logbook is disabled.",
            )

    async def get_location_logbook_settings(
        self,
        user_id: int,
        location_id: int,
    ) -> LocationLogbookSettingsResponse:
        """Get logbook settings for a location."""
        location = await self._assert_location_exists(location_id)
        await self._assert_user_can_access_location(user_id, location)

        settings = await self._get_settings_by_location_id(location_id)
        if not settings:
            return LocationLogbookSettingsResponse(
                location_id=location_id,
                is_enabled=False,
                updated_by=None,
                updated_at=None,
            )

        return LocationLogbookSettingsResponse(
            location_id=settings.location_id,
            is_enabled=settings.is_enabled,
            updated_by=settings.updated_by,
            updated_at=settings.updated_at,
        )

    async def update_location_logbook_settings(
        self,
        user_id: int,
        location_id: int,
        payload: LocationLogbookSettingsUpdateRequest,
    ) -> LocationLogbookSettingsResponse:
        """Enable or disable logbook for a location."""
        location = await self._assert_location_exists(location_id)
        await self._assert_user_can_access_location(user_id, location)

        settings = await self._get_settings_by_location_id(location_id)
        if not settings:
            settings = LocationLogbookSettings(
                location_id=location_id,
                is_enabled=payload.enabled,
                updated_by=user_id,
                updated_at=datetime.now(),
            )
            self.session.add(settings)
            await self.session.commit()
            await self.session.refresh(settings)
        else:
            settings.is_enabled = payload.enabled
            settings.updated_by = user_id
            settings.updated_at = datetime.now()
            self.session.add(settings)
            await self.session.commit()
            await self.session.refresh(settings)

        return LocationLogbookSettingsResponse(
            location_id=settings.location_id,
            is_enabled=settings.is_enabled,
            updated_by=settings.updated_by,
            updated_at=settings.updated_at,
        )

    async def create_logbook_entry(
        self,
        user_id: int,
        payload: LocationLogbookCreateRequest,
    ):
        """Create a logbook entry."""
        location = await self._assert_location_exists(payload.location_id)
        await self._assert_user_can_access_location(user_id, location)
        await self._assert_logbook_enabled(payload.location_id)

        data_model = payload.model_dump(exclude_none=True)
        entry = LocationLogbook(
            created_by=user_id,
            **data_model,
            created_at=datetime.now(),
        )

        self.session.add(entry)
        await self.session.commit()
        await self.session.refresh(entry)

    async def list_location_logbook_entries(
        self,
        user_id: int,
        location_id: int,
        params: Params,
    ) -> Page[LocationLogbookResponse]:
        """List logbook entries for a location."""
        location = await self._assert_location_exists(location_id)
        await self._assert_user_can_access_location(user_id, location)
        await self._assert_logbook_enabled(location_id)

        stmt = (
            select(LocationLogbook)
            .where(LocationLogbook.location_id == location_id)
            .options(
                selectinload(LocationLogbook.location),
                selectinload(LocationLogbook.creator),
            )
            .order_by(desc(LocationLogbook.created_at))
        )

        return await paginate(
            self.session,
            stmt,
            params,
            transformer=lambda items: [
                LocationLogbookResponse(
                    id=entry.id,
                    location_id=entry.location_id,
                    created_by=entry.created_by,
                    description=entry.description,
                    media_url=self.azure_service.generate_read_sas_url(
                        container_name="location-logbook",
                        blob_name=entry.media_name,
                    )
                    if entry.media_name
                    else None,
                    media_type=entry.media_type,
                    created_at=entry.created_at,
                    location_name=entry.location.name if entry.location else None,
                    location_address=entry.location.address if entry.location else None,
                    user_full_name=entry.creator.full_name if entry.creator else None,
                )
                for entry in cast(List[LocationLogbook], items)
            ],
        )

    async def create_police_access_path(
        self,
        user_id: int,
        location_id: int,
    ) -> PoliceLinkResponse:
        """Create a police access link for a location logbook."""
        location = await self._assert_location_exists(location_id)
        await self._assert_user_can_access_location(user_id, location)
        await self._assert_logbook_enabled(location_id)

        police_access = await self.session.execute(
            select(PoliceAccessPermit)
            .where(PoliceAccessPermit.location_id == location_id)
            .where(PoliceAccessPermit.expires_at > datetime.now())
        )
        existing_permit = police_access.scalar_one_or_none()

        if existing_permit:
            return PoliceLinkResponse(
                relative_path=f"/location-logbook/police-view/{existing_permit.token}",
                expires_at=existing_permit.expires_at,
            )

        token = create_secret_token_urlsafe()
        expires_at = datetime.now() + timedelta(minutes=30)

        new_police_access = PoliceAccessPermit(
            location_id=location_id,
            created_by=user_id,
            token=token,
            expires_at=expires_at,
        )

        self.session.add(new_police_access)
        await self.session.commit()
        await self.session.refresh(new_police_access)

        return PoliceLinkResponse(
            relative_path=f"/location-logbook/police-view/{token}",
            expires_at=expires_at,
        )

    async def view_logs_police(
        self,
        token: str,
    ) -> PoliceViewResponse:
        """View logbook entries via police access token."""
        result = await self.session.execute(
            select(PoliceAccessPermit)
            .options(selectinload(PoliceAccessPermit.location))
            .where(PoliceAccessPermit.token == token)
        )
        police_access = result.scalar_one_or_none()

        if not police_access:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Access to logbook not found.",
            )

        if police_access.expires_at < datetime.now():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access to logbook has expired.",
            )

        stmt = (
            select(LocationLogbook)
            .where(LocationLogbook.location_id == police_access.location_id)
            .options(
                selectinload(LocationLogbook.location),
                selectinload(LocationLogbook.creator),
            )
            .order_by(desc(LocationLogbook.created_at))
        )
        entries_result = await self.session.execute(stmt)
        entries = entries_result.scalars().all()

        location_name = None
        if police_access.location:
            location_name = police_access.location.name

        response_entries = [
            LocationLogbookResponse(
                id=entry.id,
                location_id=entry.location_id,
                created_by=entry.created_by,
                description=entry.description,
                media_url=self.azure_service.generate_read_sas_url(
                    container_name="location-logbook",
                    blob_name=entry.media_name,
                )
                if entry.media_name
                else None,
                media_type=entry.media_type,
                created_at=entry.created_at,
                location_name=entry.location.name if entry.location else None,
                location_address=entry.location.address if entry.location else None,
                user_full_name=entry.creator.full_name if entry.creator else None,
            )
            for entry in entries[:100]
        ]

        return PoliceViewResponse(
            location_name=location_name or "Location",
            entries=response_entries,
        )
