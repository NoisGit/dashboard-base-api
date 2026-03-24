"""Location service module for the Sentinel Enterprise API."""

# pylint: disable=no-member, singleton-comparison

from datetime import datetime, date
from typing import List, Optional, cast

from fastapi import HTTPException, status
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select, desc, or_

from src.core.enums import UserRole, CustomFormFieldType
from src.models import (
    Location,
    Company,
    CompanyStaff,
    UserLocationAccess,
    CompanyLocationAccess,
    CustomForm,
    CustomFormField,
    AccessList,
    ExternalPeople,
    TypeAccessList,
    User,
)
from src.schemas import (
    LocationCreateRequest,
    LocationUpdateRequest,
    LocationAssignCompanyRequest,
    LocationAssignUserRequest,
    LocationResponse,
    AccessListResponse,
    JanitorResponse,
)
from src.schemas.location_custom_form_schemas import (
    LocationCustomFormResponse,
    LocationCustomFormUpsertRequest,
    LocationCustomFieldUpdateRequest,
    LocationCustomFieldResponse,
)
from src.services import UserService, CompanyService, AzureService

MAX_CUSTOM_FIELDS_PER_LOCATION = 4


class LocationService:
    """Service for location operations."""

    def __init__(
        self,
        session: AsyncSession,
        azure_service: AzureService,
        user_service: UserService,
        company_service: CompanyService
    ):
        self.session = session
        self.azure_service = azure_service
        self.user_service = user_service
        self.company_service = company_service

    async def _get_location_by_id(
        self,
        location_id: int,
    ) -> Optional[Location]:
        stmt = select(Location).where(Location.id == location_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_location_by_id(self, location_id: int) -> Optional[Location]:
        """Public helper to retrieve a location by ID."""
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
            company_id = my_company_id

        stmt = (
            select(Location)
            .where(Location.is_active == True)
            .options(selectinload(Location.company_locations_accesses))
        )

        if company_id is not None:
            stmt = (
                stmt.join(
                    CompanyLocationAccess,
                    CompanyLocationAccess.location_id == Location.id,
                )
                .where(CompanyLocationAccess.company_id == company_id)
            )

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
                    logo=self.azure_service.generate_read_sas_url(
                        container_name="locations",
                        blob_name=location.logo,
                    ) if location.logo else None,
                    company_ids=[
                        access.company_id
                        for access in location.company_locations_accesses
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
        """Get location detail."""
        return await self.check_user_permission_on_location(
            user_id=user_id,
            location_id=location_id,
        )

    async def create_location(
        self,
        user_id: int,
        payload: LocationCreateRequest,
    ):
        """Create a location."""
        location = Location(
            name=payload.name,
            address=payload.address,
            country=payload.country,
            logo=payload.logo,
            is_active=True,
            created_by=user_id,
            created_at=datetime.now(),
        )

        self.session.add(location)
        await self.session.commit()

    async def update_location(
        self,
        location_id: int,
        payload: LocationUpdateRequest,
    ):
        """Update a location."""
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

    async def soft_delete_location(
        self,
        location_id: int,
    ):
        """Soft delete a location."""
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
    ):
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

    async def assign_user_to_location(
        self,
        requester_id: int,
        location_id: int,
        payload: LocationAssignUserRequest,
    ):
        """Assign a user to a location."""
        await self.check_user_permission_on_location(
            user_id=requester_id,
            location_id=location_id,
        )

        companies_stmt = select(CompanyLocationAccess.company_id).where(
            CompanyLocationAccess.location_id == location_id,
        )
        companies_result = await self.session.execute(companies_stmt)
        company_ids = [row[0] for row in companies_result.all()]

        if not company_ids:
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

        if target_user.role != UserRole.JANITOR:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only janitors can be assigned to locations.",
            )

        staff_stmt = select(CompanyStaff).where(
            CompanyStaff.user_id == payload.user_id,
            CompanyStaff.company_id.in_(company_ids),
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
        """Validate access to a location."""
        user = await self.user_service.get_user_by_id(user_id)
        if not user or not user.is_active:
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

    async def get_location_custom_form(
        self,
        user_id: int,
        location_id: int,
    ) -> LocationCustomFormResponse:
        """Get custom form for a location."""
        await self.check_user_permission_on_location(
            user_id=user_id,
            location_id=location_id,
        )

        stmt = (
            select(CustomForm)
            .where(
                CustomForm.location_id == location_id,
                CustomForm.is_active == True,
            )
            .options(selectinload(CustomForm.fields))
        )
        result = await self.session.execute(stmt)
        form = result.scalars().first()

        if not form:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Custom form not found.",
            )

        active_fields = [
            f for f in form.fields if getattr(f, "is_active", True)]

        return LocationCustomFormResponse(
            id=form.id,
            location_id=form.location_id,
            is_active=form.is_active,
            created_by=form.created_by,
            created_at=form.created_at,
            updated_at=form.updated_at,
            fields=[
                LocationCustomFieldResponse(
                    id=f.id,
                    form_id=f.form_id,
                    name=f.name,
                    field_type=f.field_type,
                    options=f.options,
                    is_required=f.is_required,
                    display_order=f.display_order,
                    allow_image=getattr(f, "allow_image", False),
                    is_active=f.is_active,
                    created_at=f.created_at,
                )
                for f in active_fields
            ],
        )

    async def create_location_custom_form_fields(
        self,
        user_id: int,
        location_id: int,
        payload: LocationCustomFormUpsertRequest,
    ):
        """Create custom form fields for a location."""
        await self.check_user_permission_on_location(
            user_id=user_id,
            location_id=location_id,
        )

        if not payload.fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="fields is required.",
            )

        stmt = (
            select(CustomForm)
            .where(
                CustomForm.location_id == location_id,
                CustomForm.is_active == True,
            )
            .options(selectinload(CustomForm.fields))
        )
        result = await self.session.execute(stmt)
        form = result.scalars().first()

        existing_active_fields = []
        if form:
            existing_active_fields = [
                f for f in form.fields if getattr(f, "is_active", True)
            ]

        if len(existing_active_fields) + len(payload.fields) > MAX_CUSTOM_FIELDS_PER_LOCATION:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Maximum {MAX_CUSTOM_FIELDS_PER_LOCATION} fields allowed.",
            )

        names = set()
        for existing in existing_active_fields:
            existing_name = (getattr(existing, "name", None) or "").strip()
            if existing_name:
                names.add(existing_name.lower())

        cleaned_fields = []
        for field in payload.fields:
            field_name = (field.name or "").strip()
            if not field_name:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Field name is required.",
                )

            lowered = field_name.lower()
            if lowered in names:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Field names must be unique.",
                )
            names.add(lowered)

            requires_options = field.field_type in (
                CustomFormFieldType.DROPDOWN,
                CustomFormFieldType.RADIO,
                CustomFormFieldType.CHECKBOX,
            )

            options = None
            if field.options is not None:
                options = [o.strip() for o in field.options if o and o.strip()]

            if requires_options:
                if not options:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="options is required for this field type.",
                    )
                lowered_opts = [o.lower() for o in options]
                if len(set(lowered_opts)) != len(lowered_opts):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="options must be unique.",
                    )
            else:
                if field.options is not None:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="options is not allowed for this field type.",
                    )

            cleaned_fields.append(
                {
                    "name": field_name,
                    "field_type": field.field_type,
                    "options": options if requires_options else None,
                    "is_required": field.is_required,
                    "display_order": field.display_order,
                    "allow_image": field.allow_image,
                }
            )

        now = datetime.now()

        if not form:
            form = CustomForm(
                location_id=location_id,
                is_active=True,
                created_by=user_id,
                created_at=now,
                updated_at=None,
            )
            self.session.add(form)
            await self.session.commit()
            await self.session.refresh(form)
        else:
            form.updated_at = now
            self.session.add(form)
            await self.session.commit()
            await self.session.refresh(form)

        for field in cleaned_fields:
            new_field = CustomFormField(
                form_id=form.id,
                name=field["name"],
                field_type=field["field_type"],
                options=field["options"],
                is_required=field["is_required"],
                display_order=field["display_order"],
                is_active=True,
                created_at=now,
            )

            if hasattr(new_field, "allow_image"):
                new_field.allow_image = field["allow_image"]

            self.session.add(new_field)

        await self.session.commit()

    async def update_location_custom_form_field(
        self,
        user_id: int,
        location_id: int,
        custom_form_field_id: int,
        payload: LocationCustomFieldUpdateRequest,
    ):
        """Update a custom form field for a location."""
        await self.check_user_permission_on_location(
            user_id=user_id,
            location_id=location_id,
        )

        stmt = (
            select(CustomFormField)
            .join(CustomForm, CustomForm.id == CustomFormField.form_id)
            .where(
                CustomForm.location_id == location_id,
                CustomForm.is_active == True,
                CustomFormField.id == custom_form_field_id,
            )
        )
        result = await self.session.execute(stmt)
        field = result.scalars().first()

        if not field or not getattr(field, "is_active", True):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Custom form field not found.",
            )

        update_data = payload.model_dump(exclude_none=True)

        if "name" in update_data:
            new_name = (update_data.get("name") or "").strip()
            if not new_name:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Field name is required.",
                )

            name_stmt = select(CustomFormField).where(
                CustomFormField.form_id == field.form_id,
                CustomFormField.is_active == True,
            )
            name_result = await self.session.execute(name_stmt)
            siblings = name_result.scalars().all()

            for sib in siblings:
                if sib.id != field.id and (sib.name or "").strip().lower() == new_name.lower():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Field names must be unique.",
                    )

            field.name = new_name

        new_field_type = field.field_type
        if "field_type" in update_data:
            new_field_type = update_data["field_type"]
            field.field_type = new_field_type

        requires_options = new_field_type in (
            CustomFormFieldType.DROPDOWN,
            CustomFormFieldType.RADIO,
            CustomFormFieldType.CHECKBOX,
        )

        if "options" in update_data:
            raw_options = update_data.get("options")
            cleaned_options = None
            if raw_options is not None:
                cleaned_options = [o.strip()
                                   for o in raw_options if o and o.strip()]

            if requires_options:
                if not cleaned_options:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="options is required for this field type.",
                    )
                lowered_opts = [o.lower() for o in cleaned_options]
                if len(set(lowered_opts)) != len(lowered_opts):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="options must be unique.",
                    )
                field.options = cleaned_options
            else:
                if raw_options is not None:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="options is not allowed for this field type.",
                    )
                field.options = None
        else:
            if "field_type" in update_data and not requires_options:
                field.options = None

            if "field_type" in update_data and requires_options and not field.options:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="options is required for this field type.",
                )

        if "is_required" in update_data:
            field.is_required = update_data["is_required"]

        if "display_order" in update_data:
            field.display_order = update_data["display_order"]

        if "allow_image" in update_data and hasattr(field, "allow_image"):
            field.allow_image = update_data["allow_image"]

        self.session.add(field)
        await self.session.commit()

        form = await self.session.get(CustomForm, field.form_id)
        if form:
            form.updated_at = datetime.now()
            self.session.add(form)
            await self.session.commit()

    async def get_location_access_lists(
        self,
        user_id: int,
        location_id: int,
        include_expired: bool = False,
    ) -> List[AccessListResponse]:
        """Access list by location."""
        await self.check_user_permission_on_location(user_id, location_id)

        stmt = (
            select(
                AccessList.id,
                AccessList.location_id,
                AccessList.name.label("full_name"),
                AccessList.reason,
                AccessList.vehicle_plate,
                AccessList.expiration_date,
                AccessList.created_at,
                ExternalPeople.id_number,
                TypeAccessList.name.label("type_access_list"),
            )
            .join(
                ExternalPeople,
                ExternalPeople.id == AccessList.external_people_id,
            )
            .join(
                TypeAccessList,
                TypeAccessList.id == AccessList.type_access_list_id,
            )
            .where(
                AccessList.location_id == location_id,
            )
            .order_by(desc(AccessList.created_at))
        )

        if not include_expired:
            today = date.today()
            stmt = stmt.where(
                or_(
                    AccessList.expiration_date == None,
                    AccessList.expiration_date >= today,
                )
            )

        result = await self.session.execute(stmt)
        res_access_list = result.mappings().all()

        return [
            AccessListResponse(
                id=accessList.id,
                location_id=accessList.location_id,
                full_name=accessList.full_name,
                reason=accessList.reason,
                vehicle_plate=accessList.vehicle_plate,
                expiration_date=accessList.expiration_date,
                created_at=accessList.created_at,
                id_number=accessList.id_number,
                type_access_list=accessList.type_access_list,
            )
            for accessList in res_access_list
        ]

    async def list_janitors(
        self,
        user_id: int,
        location_id: int,
        search: Optional[str],
        params: Params,
    ) -> Page[JanitorResponse]:
        """Return Janitors of a location."""
        user = await self.user_service.get_user_by_id(user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        stmt = select(User) \
            .where(User.is_active == True) \
            .where(User.role == UserRole.JANITOR)

        if search:
            like_pattern = f"%{search}%"
            stmt = stmt.where(
                (User.full_name.ilike(like_pattern))
                | (User.username.ilike(like_pattern)),
            )

        if user.role != UserRole.SUPERADMIN:
            location_access = await self.check_user_permission_on_location(user_id, location_id)
            if not location_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User does not have access to the specified location.",
                )
            else:
                stmt = (
                    stmt.join(
                        UserLocationAccess,
                        UserLocationAccess.user_id == User.id,
                    )
                    .where(UserLocationAccess.location_id == location_id)
                )
        else:
            stmt = (
                stmt.join(
                    UserLocationAccess,
                    UserLocationAccess.user_id == User.id,
                )
                .where(UserLocationAccess.location_id == location_id)
            )

        return await paginate(
            self.session,
            stmt,
            params,
            transformer=lambda items: [
                JanitorResponse(
                    id=user.id,
                    username=user.username,
                    full_name=user.full_name,
                    email=user.email,
                    role=user.role,
                    status=user.status,
                    is_active=user.is_active,
                    plan_id=user.plan_id,
                    created_at=user.created_at,
                )
                for user in cast(List[User], items)
            ],
        )
