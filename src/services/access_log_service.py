"""Access log service module for Sentinel Enterprise API."""
from datetime import datetime, date
from typing import Optional, List

from fastapi import HTTPException, status
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select, desc


from src.services.azure_service import AzureService
from src.services.user_service import UserService
from src.services.location_service import LocationService

from src.models import AccessLog, AccessLogImage, ExternalPeople
from src.core.enums import AccessLogImageType, UserRole
from src.schemas.access_log_schemas import (
    AccessLogResponse,
    AccessLogCreateRequest,
    AccessLogExitRequest,
    ExternalPeopleResponse,
)


class AccessLogService:
    """Service for access log operations."""

    def __init__(
        self,
        session: AsyncSession,
        azure_service: AzureService,
        user_service: UserService,
        location_service: LocationService,
    ):
        self.session = session
        self.azure_service = azure_service
        self.user_service = user_service
        self.location_service = location_service

    async def get_active_entries(self, location_id: int, user_id: int) -> List[AccessLogResponse]:
        """
        Get active access logs for a specific location.
        Active = entry exists but no exit_date (person is still inside).
        """

        await self.location_service.check_user_permission_on_location(
            user_id=user_id,
            location_id=location_id,
        )

        result = await self.session.execute(
            select(AccessLog)
            .options(selectinload(AccessLog.images))
            .options(selectinload(AccessLog.external_people))
            .where(AccessLog.location_id == location_id)
            .where(AccessLog.exit_date == None)  # pylint: disable=singleton-comparison
            .order_by(desc(AccessLog.created_at))
        )
        logs = list(result.scalars().all())
        return [self._convert_to_response(log) for log in logs]

    async def get_today_exits(self, location_id: int, user_id: int) -> List[AccessLogResponse]:
        """
        Get exits from today for a specific location.
        Returns logs with exit_date set to today.
        """

        await self.location_service.check_user_permission_on_location(
            user_id=user_id,
            location_id=location_id,
        )

        today_start = datetime.combine(date.today(), datetime.min.time())
        today_end = datetime.combine(date.today(), datetime.max.time())

        result = await self.session.execute(
            select(AccessLog)
            .options(selectinload(AccessLog.images))
            .options(selectinload(AccessLog.external_people))
            .where(AccessLog.location_id == location_id)
            .where(AccessLog.exit_date != None)  # pylint: disable=singleton-comparison
            .where(AccessLog.exit_date >= today_start)
            .where(AccessLog.exit_date <= today_end)
            .order_by(desc(AccessLog.exit_date))
        )
        logs = list(result.scalars().all())

        return [self._convert_to_response(log) for log in logs]

    async def create_access_log(
        self,
        payload: AccessLogCreateRequest,
        created_by: int,
    ) -> AccessLogResponse:
        """
        Create a new access log entry (person entering).
        Only JANITOR role should call this.
        """
        access_log = AccessLog(
            location_id=payload.location_id,
            external_people_id=payload.external_people_id,
            created_by=created_by,
            type_document=payload.type_document,
            vehicle_plate=payload.vehicle_plate,
            office=payload.office,
            comment=payload.comment,
            custom_form_responses=payload.custom_form_responses,
            created_at=datetime.now(),
        )

        self.session.add(access_log)
        await self.session.flush()

        # Add entry images
        if payload.entry_images:
            for image_name in payload.entry_images:
                image = AccessLogImage(
                    access_log_id=access_log.id,
                    image_name=image_name,
                    image_type=AccessLogImageType.ENTRY,
                )
                self.session.add(image)

        await self.session.commit()

        # Reload with relationships
        result = await self.session.execute(
            select(AccessLog)
            .options(selectinload(AccessLog.images))
            .options(selectinload(AccessLog.external_people))
            .where(AccessLog.id == access_log.id)
        )
        access_log = result.scalar_one()

        return self._convert_to_response(access_log)

    async def register_exit(
        self,
        access_log_id: int,
        payload: AccessLogExitRequest,
        exit_created_by: int,
    ) -> AccessLogResponse:
        """
        Register exit for an existing access log.
        Only JANITOR role should call this.
        """
        result = await self.session.execute(
            select(AccessLog)
            .options(selectinload(AccessLog.images))
            .options(selectinload(AccessLog.external_people))
            .where(AccessLog.id == access_log_id)
        )
        access_log = result.scalar_one_or_none()

        if not access_log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Access log not found",
            )

        if access_log.exit_date is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Exit already registered for this access log",
            )

        # Update exit info
        access_log.exit_date = datetime.now()
        access_log.exit_comment = payload.exit_comment
        access_log.exit_created_by = exit_created_by

        # Add exit images
        if payload.exit_images:
            for image_name in payload.exit_images:
                image = AccessLogImage(
                    access_log_id=access_log.id,
                    image_name=image_name,
                    image_type=AccessLogImageType.EXIT,
                )
                self.session.add(image)

        await self.session.commit()

        # Reload with updated images
        result = await self.session.execute(
            select(AccessLog)
            .options(selectinload(AccessLog.images))
            .options(selectinload(AccessLog.external_people))
            .where(AccessLog.id == access_log.id)
        )
        access_log = result.scalar_one()

        return self._convert_to_response(access_log)

    # =========================================================================
    # DASHBOARD - Admin Methods (Paginated)
    # =========================================================================

    async def get_logs_paginated(  # pylint: disable=too-many-arguments, too-many-positional-arguments
        self,
        location_id: int,
        user_id: int,
        params: Params,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status_filter: Optional[str] = None,
        search_plate: Optional[str] = None,
        search_name: Optional[str] = None,
        search_dni: Optional[str] = None,
    ) -> Page[AccessLogResponse]:
        """
        Get access logs with filters and pagination for dashboard.
        Always filters by a specific location.
        """

        await self.location_service.check_user_permission_on_location(
            user_id=user_id,
            location_id=location_id,
        )

        query = (
            select(AccessLog)
            .options(selectinload(AccessLog.images))
            .options(selectinload(AccessLog.external_people))
            .options(selectinload(AccessLog.location))
            .where(AccessLog.location_id == location_id)
        )

        # Filter by date range
        if start_date:
            query = query.where(AccessLog.created_at >= start_date)
        if end_date:
            query = query.where(AccessLog.created_at <= end_date)

        # Filter by status
        if status_filter == "active":
            query = query.where(
                AccessLog.exit_date == None  # pylint: disable=singleton-comparison
            )
        elif status_filter == "completed":
            query = query.where(
                AccessLog.exit_date != None  # pylint: disable=singleton-comparison
            )

        # Search filters
        # Search by vehicle plate (no JOIN needed)
        if search_plate:
            # pylint: disable=no-member
            query = query.where(
                AccessLog.vehicle_plate.ilike(f"%{search_plate}%")
            )
            # pylint: enable=no-member

        # Search by person name or DNI (requires JOIN with ExternalPeople)
        if search_name or search_dni:
            query = query.outerjoin(
                ExternalPeople, AccessLog.external_people_id == ExternalPeople.id
            )
            if search_name:
                # pylint: disable=no-member
                query = query.where(
                    ExternalPeople.name.ilike(f"%{search_name}%")
                )
                # pylint: enable=no-member
            if search_dni:
                # pylint: disable=no-member
                query = query.where(
                    ExternalPeople.id_number.ilike(f"%{search_dni}%")
                )
                # pylint: enable=no-member

        # Order by most recent first
        query = query.order_by(desc(AccessLog.created_at))

        # Get paginated results and transform
        return await paginate(
            self.session,
            query,
            params,
            transformer=lambda items: [
                self._convert_to_response(item) for item in items
            ]
        )

    def _convert_image_to_response(self, image_name: str) -> str:
        """Convert AccessLogImage model to schema."""
        return self.azure_service.generate_read_sas_url(
            container_name="access-logs",
            blob_name=image_name
        )

    def _convert_to_response(self, access_log: AccessLog) -> AccessLogResponse:
        """Convert AccessLog model to AccessLogResponse schema."""
        # Separate images by type (entry vs exit)
        entry_images = []
        exit_images = []

        if access_log.images:
            for img in access_log.images:
                image_url = self._convert_image_to_response(img.image_name)
                if img.image_type == AccessLogImageType.ENTRY:
                    entry_images.append(image_url)
                elif img.image_type == AccessLogImageType.EXIT:
                    exit_images.append(image_url)

        # Convert external people if loaded
        external_people = None
        if access_log.external_people:
            external_people = ExternalPeopleResponse(
                id=access_log.external_people.id,
                name=access_log.external_people.name,
                id_number=access_log.external_people.id_number,
                gender=access_log.external_people.gender,
                file_name=access_log.external_people.file_name,
            )

        return AccessLogResponse(
            id=access_log.id,
            location_id=access_log.location_id,
            external_people_id=access_log.external_people_id,
            type_document=access_log.type_document,
            vehicle_plate=access_log.vehicle_plate,
            office=access_log.office,
            comment=access_log.comment,
            entry_images=entry_images if entry_images else None,
            exit_date=access_log.exit_date,
            exit_comment=access_log.exit_comment,
            exit_created_by=access_log.exit_created_by,
            exit_images=exit_images if exit_images else None,
            created_by=access_log.created_by,
            created_at=access_log.created_at,
            custom_form_responses=access_log.custom_form_responses,
            external_people=external_people,
        )
