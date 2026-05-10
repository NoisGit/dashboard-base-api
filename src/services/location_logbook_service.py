"""Location logbook service module for the Coredeck API."""

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
from src.models import (
    LocationLogbook,
    LocationLogbookSettings,
    PoliceAccessPermit,
)
from src.schemas import (
    LocationLogbookCreateRequest,
    LocationLogbookResponse,
    LocationLogbookSettingsResponse,
    LocationLogbookSettingsUpdateRequest,
    PoliceLinkResponse,
    PoliceViewResponse,
)
from src.services.storage_service import StorageService
from src.services.location_service import LocationService


class LocationLogbookService:
    """Service for location logbook operations."""

    def __init__(
        self,
        session: AsyncSession,
        storage_service: StorageService,
        location_service: LocationService,
    ):
        self.session = session
        self.storage_service = storage_service
        self.location_service = location_service

    async def _get_settings_by_location_id(
        self,
        location_id: int,
    ) -> Optional[LocationLogbookSettings]:
        stmt = select(LocationLogbookSettings).where(
            LocationLogbookSettings.location_id == location_id
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

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
        await self.location_service.check_user_permission_on_location(
            user_id=user_id,
            location_id=location_id,
        )

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
        await self.location_service.check_user_permission_on_location(
            user_id=user_id,
            location_id=location_id,
        )

        settings = await self._get_settings_by_location_id(location_id)
        now = datetime.now()

        if not settings:
            settings = LocationLogbookSettings(
                location_id=location_id,
                is_enabled=payload.enabled,
                updated_by=user_id,
                updated_at=now,
            )
            self.session.add(settings)
            await self.session.commit()
            await self.session.refresh(settings)
        else:
            settings.is_enabled = payload.enabled
            settings.updated_by = user_id
            settings.updated_at = now
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
        await self.location_service.check_user_permission_on_location(
            user_id=user_id,
            location_id=payload.location_id,
        )
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
        await self.location_service.check_user_permission_on_location(
            user_id=user_id,
            location_id=location_id,
        )
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
                    media_url=self.storage_service.generate_read_url(
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
        await self.location_service.check_user_permission_on_location(
            user_id=user_id,
            location_id=location_id,
        )
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

        location_name = (
            police_access.location.name
            if police_access.location
            else "Location"
        )

        response_entries = [
            LocationLogbookResponse(
                id=entry.id,
                location_id=entry.location_id,
                created_by=entry.created_by,
                description=entry.description,
                media_url=self.storage_service.generate_read_url(
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
            location_name=location_name,
            entries=response_entries,
        )
