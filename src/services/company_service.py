"""Company service module for the Sentinel Enterprise API."""

from typing import List, Optional, cast

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.core.enums import UserRole
from src.models import Company, CompanyStaff
from src.schemas import CompanyCreateRequest, CompanyUpdateRequest
from src.services.user_service import UserService

# pylint: disable=no-member, singleton-comparison
# noqa: E712


class CompanyService:
    """Service for company operations and RBAC."""

    def __init__(
        self,
        session: AsyncSession,
        user_service: Optional[UserService] = None,
    ) -> None:
        self.session = session
        self.user_service = user_service or UserService(session)

    async def _ensure_user_linked_to_company(
        self,
        company_id: int,
        user_id: int,
        role: UserRole,
    ) -> None:
        """Ensure the user is linked to the company (SUPERADMIN bypasses)."""
        if role is UserRole.SUPERADMIN:
            return

        stmt = (
            select(CompanyStaff)
            .where(CompanyStaff.company_id == company_id)
            .where(CompanyStaff.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        link = result.scalars().first()

        if not link:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to access this company.",
            )

    async def _get_company_by_id(self, company_id: int) -> Optional[Company]:
        return await self.session.get(Company, company_id)

    async def list_companies(
        self,
        user_id: int,
        role: UserRole,
    ) -> List[Company]:
        """List active companies visible for the current user."""
        if role is UserRole.SUPERADMIN:
            stmt = select(Company).where(Company.is_active == True)  # noqa: E712
        else:
            stmt = (
                select(Company)
                .join(CompanyStaff, CompanyStaff.company_id == Company.id)
                .where(CompanyStaff.user_id == user_id)
                .where(Company.is_active == True)  # noqa: E712
            )

        result = await self.session.execute(stmt)
        companies = result.scalars().all()
        return cast(List[Company], companies)

    async def get_company_detail(
        self,
        user_id: int,
        role: UserRole,
        company_id: int,
    ) -> Company:
        """Get a single active company by ID if the user can access it."""
        company = await self._get_company_by_id(company_id)
        if not company or not company.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found.",
            )

        await self._ensure_user_linked_to_company(
            company_id=company_id,
            user_id=user_id,
            role=role,
        )
        return company

    async def create_company(
        self,
        requester_id: int,
        payload: CompanyCreateRequest,
    ) -> Company:
        """Create a new company."""
        company = Company(
            name=payload.name,
            activity=payload.activity,
            id_number=payload.id_number,
            logo=payload.logo,
            type_document=payload.type_document,
            created_by=requester_id,
        )

        self.session.add(company)
        await self.session.commit()
        await self.session.refresh(company)
        return company

    async def update_company(
        self,
        requester_id: int,
        requester_role: UserRole,
        company_id: int,
        payload: CompanyUpdateRequest,
    ) -> Company:
        """Update an existing company."""
        company = await self._get_company_by_id(company_id)
        if not company or not company.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found.",
            )

        await self._ensure_user_linked_to_company(
            company_id=company_id,
            user_id=requester_id,
            role=requester_role,
        )

        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(company, key, value)

        await self.session.commit()
        await self.session.refresh(company)
        return company

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
        requester_role: UserRole,
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

        await self._ensure_user_linked_to_company(
            company_id=company_id,
            user_id=requester_id,
            role=requester_role,
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
        await self.session.refresh(assignment)
