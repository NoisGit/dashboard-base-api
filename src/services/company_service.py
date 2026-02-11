"""Company service module for the Sentinel Enterprise API."""

from typing import List, Optional, cast
from datetime import datetime

from fastapi_pagination import Params, Page
from fastapi_pagination.ext.sqlalchemy import paginate
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, desc
from src.core.enums import UserRole


from src.models import Company, CompanyStaff, User
from src.schemas import (
    CompanyCreateRequest,
    CompanyUpdateRequest,
    CompanyResponse,
    UserCreateRequest,
    SubCompanyCreateRequest,
    EmptyResponse,
)
from src.services.user_service import UserService


class CompanyService:
    """Service for company operations."""

    def __init__(
        self,
        session: AsyncSession,
        user_service: Optional[UserService] = None,
    ) -> None:
        self.session = session
        self.user_service = user_service or UserService(session)

    async def _get_company_by_id(self, company_id: int) -> Optional[CompanyResponse]:
        return await self.session.get(Company, company_id)

    async def list_companies(self, params: Params) -> Page[CompanyResponse]:
        """List active companies."""
        stmt = select(Company).where(Company.is_active == True)
        return await paginate(
            self.session,
            stmt,
            params,
            transformer=lambda items: [
                CompanyResponse(
                    id=company.id,
                    name=company.name,
                    activity=company.activity,
                    id_number=company.id_number,
                    logo=company.logo,
                    type_document=company.type_document,
                    is_active=company.is_active,
                    created_by=company.created_by,
                    created_at=company.created_at,
                )
                for company in cast(List[Company], items)
            ],
        )

    async def get_company_detail(
        self,
        company_id: int,
    ) -> Company:
        """Get a single active company by ID."""
        company = await self._get_company_by_id(company_id)
        if not company or not company.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found.",
            )

        return company

    async def create_company(
        self,
        user_id: int,
        payload: CompanyCreateRequest,
    ) -> EmptyResponse:
        """Create a new company."""
        company = Company(
            name=payload.name,
            activity=payload.activity,
            id_number=payload.id_number,
            logo=payload.logo,
            type_document=payload.type_document,
            created_by=user_id,
        )

        self.session.add(company)
        await self.session.commit()
        await self.session.refresh(company)
        return EmptyResponse()

    async def create_subcompany(
        self,
        user_id: int,
        payload: SubCompanyCreateRequest,
    ) -> EmptyResponse:
        """Create a new sub company."""
        user = await self.user_service.get_user_by_id(user_id)
        if not user or not getattr(user, "is_active", True):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        if user.role != UserRole.SUPERADMIN:
            parent_company_id = await self.get_company_id_by_user_id(user_id)
        else:
            parent_company_id = payload.parent_company_id

        subcompany = Company(
            name=payload.name,
            activity=payload.activity,
            id_number=payload.id_number,
            parent_company_id=parent_company_id,
            logo=payload.logo,
            type_document=payload.type_document,
            created_by=user_id,
        )

        self.session.add(subcompany)
        await self.session.commit()
        await self.session.refresh(subcompany)
        return EmptyResponse()

    async def update_company(
        self,
        company_id: int,
        payload: CompanyUpdateRequest,
    ) -> EmptyResponse:
        """Update an existing company."""
        company = await self._get_company_by_id(company_id)
        if not company or not company.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found.",
            )

        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(company, key, value)

        await self.session.commit()
        await self.session.refresh(company)
        return EmptyResponse()

    async def soft_delete_company(
        self,
        company_id: int,
    ):
        """Soft delete a company by setting is_active = False."""
        company = await self._get_company_by_id(company_id)
        if not company or not company.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found.",
            )

        company.is_active = False
        await self.session.commit()

    async def assign_user_to_company(
        self,
        requester_id: int,
        company_id: int,
        user_id: int,
    ):
        """Assign an existing user to a company."""
        company = await self._get_company_by_id(company_id)
        if not company or not company.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found.",
            )

        user = await self.user_service.get_user_by_id(user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        assignment_stmt = select(CompanyStaff).where(
            CompanyStaff.user_id == user_id,
        )
        assignment_result = await self.session.execute(assignment_stmt)
        existing_assignment = assignment_result.scalars().first()

        if existing_assignment:
            if existing_assignment.company_id == company_id:
                return

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User is already assigned to another company.",
            )

        assignment = CompanyStaff(
            user_id=user_id,
            company_id=company_id,
            created_by=requester_id,
        )

        self.session.add(assignment)
        await self.session.commit()

    async def get_company_id_by_user_id(self, user_id: int) -> Optional[int]:
        """Get user's company id."""
        stmt = (
            select(CompanyStaff.company_id)
            .where(CompanyStaff.user_id == user_id)
            .order_by(desc(CompanyStaff.created_at))
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def create_user_and_assign_company(
        self,
        requester_id: int,
        company_id: int,
        payload: UserCreateRequest,
    ) -> None:
        """Create a new user."""
        check_user = await UserService.get_user_by_email(self, payload.email)
        if check_user:
            await self.assign_user_to_company(
                requester_id=requester_id,
                company_id=company_id,
                user_id=check_user.id,
            )
            return None

        await UserService._ensure_username_unique(self, payload.username)

        password_hash = UserService._hash_password(self, payload.password)

        user = User(
            username=payload.username,
            full_name=payload.full_name,
            email=payload.email,
            password_hash=password_hash,
            role=payload.role,
            plan_id=payload.plan_id,
            status=payload.status,
            is_active=True,
            created_at=datetime.now(),
        )

        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)

        await self.assign_user_to_company(
            requester_id=requester_id,
            company_id=company_id,
            user_id=user.id,
        )

        return None
