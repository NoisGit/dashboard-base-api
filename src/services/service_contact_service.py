"""Service contact service module for the Locentr API."""

import csv
import io
from typing import List, cast

from fastapi import HTTPException, UploadFile, status
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlmodel import paginate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, desc

from src.services.user_service import UserService
from src.services.location_service import LocationService
from src.models import ServiceContact
from src.schemas import (
    ServiceContactResponse,
    ServiceContactCreateRequest,
    ServiceContactUpdateRequest,
)
from src.security.uploads import validate_csv_upload

SERVICE_CONTACT_REQUIRED_CSV_HEADERS = {
    "nombre del servicio",
    "nombre del proveedor",
    "teléfono",
    "email",
}


class ServiceContactService:
    """Service for Service contact operations."""

    def __init__(
        self,
        session: AsyncSession,
        user_service: UserService,
        location_service: LocationService,
    ):
        self.session = session
        self.user_service = user_service
        self.location_service = location_service

    async def get_service_contact_by_id(
        self,
        service_contact_id: int,
    ) -> ServiceContact:
        """Get service contact by ID."""
        stmt = select(ServiceContact).where(ServiceContact.id == service_contact_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def _ensure_can_access_location(
        self,
        user_id: int,
        location_id: int,
    ) -> None:
        """Validate location access."""
        await self.location_service.check_user_permission_on_location(
            user_id=user_id,
            location_id=location_id,
        )

    async def _read_service_contact_csv(
        self,
        file: UploadFile,
    ) -> List[dict]:
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CSV file is required.",
            )

        if not file.filename.lower().endswith(".csv"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only .csv files are allowed.",
            )

        content = await file.read()
        validate_csv_upload(file, content)
        if not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CSV file is empty.",
            )

        try:
            decoded = content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CSV file must be UTF-8 encoded.",
            ) from exc

        reader = csv.DictReader(io.StringIO(decoded), delimiter=';')

        if not reader.fieldnames:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CSV headers are required.",
            )

        headers = {(header or "").strip().lower() for header in reader.fieldnames}
        missing_headers = SERVICE_CONTACT_REQUIRED_CSV_HEADERS - headers

        if missing_headers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required CSV headers: {', '.join(sorted(missing_headers))}.",
            )

        rows = []
        seen_contacts = set()

        for row_number, raw_row in enumerate(reader, start=2):
            row = {
                (key or "").strip().lower(): (value or "").strip()
                for key, value in raw_row.items()
            }

            if not any(row.values()):
                continue

            for field in SERVICE_CONTACT_REQUIRED_CSV_HEADERS:
                if not row.get(field):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"{field} is required at row {row_number}.",
                    )

            duplicate_key = (
                row["nombre del servicio"].lower(),
                row["nombre del proveedor"].lower(),
                row["email"].lower(),
                row["teléfono"],
            )

            if duplicate_key in seen_contacts:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Duplicated contact in CSV at row {row_number}.",
                )

            seen_contacts.add(duplicate_key)
            rows.append(row)

        if not rows:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CSV file does not contain valid rows.",
            )

        return rows

    async def list_service_contacts(
        self,
        location_id: int,
        user_id: int,
        params: Params,
    ) -> Page[ServiceContactResponse]:
        """List service contacts for a location."""
        await self._ensure_can_access_location(user_id, location_id)

        stmt = select(ServiceContact).where(
            ServiceContact.location_id == location_id,
        ).order_by(
            desc(ServiceContact.created_at),
        )

        return await paginate(
            self.session,
            stmt,
            params,
            transformer=lambda items: [
                ServiceContactResponse(
                    id=service_contact.id,
                    location_id=service_contact.location_id,
                    service_name=service_contact.service_name,
                    person_name=service_contact.person_name,
                    email=service_contact.email,
                    phone=service_contact.phone,
                    created_by=service_contact.created_by,
                    created_at=service_contact.created_at,
                )
                for service_contact in cast(List[ServiceContact], items)
            ]
        )

    async def create_service_contact(
        self,
        user_id: int,
        payload: ServiceContactCreateRequest
    ):
        """Create a new service contact."""
        await self._ensure_can_access_location(user_id, payload.location_id)

        new_contact = ServiceContact(
            service_name=payload.service_name,
            person_name=payload.person_name,
            email=payload.email,
            phone=payload.phone,
            location_id=payload.location_id,
            created_by=user_id,
        )

        self.session.add(new_contact)
        await self.session.commit()
        await self.session.refresh(new_contact)

    async def bulk_import_service_contacts(
        self,
        user_id: int,
        location_id: int,
        file: UploadFile,
    ) -> None:
        """Bulk import service contacts."""
        await self._ensure_can_access_location(user_id, location_id)

        rows = await self._read_service_contact_csv(file)

        for row in rows:
            stmt = select(ServiceContact).where(
                ServiceContact.location_id == location_id,
                ServiceContact.service_name == row["nombre del servicio"],
                ServiceContact.person_name == row["nombre del proveedor"],
                ServiceContact.email == row["email"],
                ServiceContact.phone == row["teléfono"],
            )
            result = await self.session.execute(stmt)
            existing_contact = result.scalars().first()

            if existing_contact:
                continue

            self.session.add(
                ServiceContact(
                    service_name=row["nombre del servicio"],
                    person_name=row["nombre del proveedor"],
                    email=row["email"],
                    phone=row["teléfono"],
                    location_id=location_id,
                    created_by=user_id,
                )
            )

        await self.session.commit()

    async def update_service_contact(
        self,
        user_id: int,
        service_contact_id: int,
        payload: ServiceContactUpdateRequest
    ):
        """Update an existing service contact."""
        service_contact = await self.get_service_contact_by_id(service_contact_id)

        if not service_contact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Service contact with id {service_contact_id} not found.",
            )

        await self._ensure_can_access_location(user_id, service_contact.location_id)

        contact_model = payload.model_dump(exclude_none=True)
        for key, value in contact_model.items():
            setattr(service_contact, key, value)

        await self.session.commit()
        await self.session.refresh(service_contact)

    async def delete_service_contact(
        self,
        user_id: int,
        service_contact_id: int,
    ) -> None:
        """Delete an existing service contact."""
        service_contact = await self.get_service_contact_by_id(service_contact_id)

        if not service_contact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Service contact with id {service_contact_id} not found.",
            )

        await self._ensure_can_access_location(user_id, service_contact.location_id)

        await self.session.delete(service_contact)
        await self.session.commit()


__all__ = ["ServiceContactService"]
