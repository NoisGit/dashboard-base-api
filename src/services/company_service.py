"""Company service module for the Sentinel Enterprise API."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.models import Company, CompanyStaff

# pylint: disable=no-member, singleton-comparison
# noqa: E712

ROLE_SUPERADMIN = "superadmin"
ROLE_ADMIN = "admin"
ROLE_SUBADMIN = "subadmin"
ROLE_JANITOR = "janitor"
ROLE_CLIENT = "client"

ROLES_CAN_VIEW_ASSOCIATED = {
    ROLE_SUPERADMIN,
    ROLE_ADMIN,
    ROLE_SUBADMIN,
    ROLE_JANITOR,
    ROLE_CLIENT,
}

ROLES_CAN_EDIT_COMPANY = {
    ROLE_SUPERADMIN,
    ROLE_ADMIN,
}

ROLES_CAN_CREATE_DELETE_COMPANY = {
    ROLE_SUPERADMIN,
}


class CompanyService:
    """Application service for company-related operations."""

    def __init__(self, session: AsyncSession):
        """Initialize the service with a database session."""
        self.session = session

    @staticmethod
    def _get_role(current_user: Dict[str, Any]) -> str:
        """Extract the role from the current user payload."""
        role = current_user.get("role")
        if role is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Role not found in token payload.",
            )
        return role

    @staticmethod
    def _get_user_id(current_user: Dict[str, Any]) -> int:
        """Extract the user_id from the current user payload."""
        user_id = current_user.get("user_id")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="user_id not found in token payload.",
            )
        return int(user_id)

    @staticmethod
    def _ensure_authenticated(current_user: Dict[str, Any]) -> None:
        """Ensure that the current user is authenticated."""
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required.",
            )

    def _ensure_can_view_companies(self, current_user: Dict[str, Any]) -> None:
        """Ensure the current user is allowed to view companies."""
        role = self._get_role(current_user)
        if role not in ROLES_CAN_VIEW_ASSOCIATED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to view companies.",
            )

    def _ensure_can_edit_companies(self, current_user: Dict[str, Any]) -> None:
        """Ensure the current user is allowed to edit companies."""
        role = self._get_role(current_user)
        if role not in ROLES_CAN_EDIT_COMPANY:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to edit companies.",
            )

    def _ensure_can_create_or_delete_companies(
        self,
        current_user: Dict[str, Any],
    ) -> None:
        """Ensure the current user is allowed to create or delete companies."""
        role = self._get_role(current_user)
        if role not in ROLES_CAN_CREATE_DELETE_COMPANY:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to create or delete companies.",
            )

    async def _ensure_user_linked_to_company(
        self,
        company_id: int,
        current_user: Dict[str, Any],
    ) -> None:
        """Ensure the current user is linked to the given company."""
        role = self._get_role(current_user)
        if role == ROLE_SUPERADMIN:
            return

        user_id = self._get_user_id(current_user)

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
        """Return a company by id or None if it does not exist."""
        return await self.session.get(Company, company_id)

    async def list_companies(
        self,
        current_user: Dict[str, Any],
    ) -> List[Company]:
        """List active companies visible for the current user."""
        self._ensure_authenticated(current_user)
        self._ensure_can_view_companies(current_user)

        role = self._get_role(current_user)
        user_id = self._get_user_id(current_user)

        if role == ROLE_SUPERADMIN:
            stmt = select(Company).where(Company.is_active == True)
        else:
            stmt = (
                select(Company)
                .join(CompanyStaff, CompanyStaff.company_id == Company.id)
                .where(CompanyStaff.user_id == user_id)
                .where(Company.is_active == True)
            )

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_company_detail(
        self,
        current_user: Dict[str, Any],
        company_id: int,
    ) -> Company:
        """Get a single active company by ID if the user can access it."""
        self._ensure_authenticated(current_user)
        self._ensure_can_view_companies(current_user)

        company = await self._get_company_by_id(company_id)
        if not company or not company.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found.",
            )

        await self._ensure_user_linked_to_company(company_id, current_user)
        return company

    async def create_company(
        self,
        current_user: Dict[str, Any],
        payload,
    ) -> Company:
        """Create a new company."""
        self._ensure_authenticated(current_user)
        self._ensure_can_create_or_delete_companies(current_user)

        user_id = self._get_user_id(current_user)

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
        return company

    async def update_company(
        self,
        current_user: Dict[str, Any],
        company_id: int,
        payload,
    ) -> Company:
        """Update an existing company."""
        self._ensure_authenticated(current_user)
        self._ensure_can_edit_companies(current_user)

        company = await self._get_company_by_id(company_id)
        if not company or not company.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found.",
            )

        await self._ensure_user_linked_to_company(company_id, current_user)

        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(company, key, value)

        await self.session.commit()
        await self.session.refresh(company)
        return company

    async def soft_delete_company(
        self,
        current_user: Dict[str, Any],
        company_id: int,
    ) -> None:
        """Soft delete a company by setting is_active to False."""
        self._ensure_authenticated(current_user)
        self._ensure_can_create_or_delete_companies(current_user)

        company = await self._get_company_by_id(company_id)
        if not company or not company.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found.",
            )

        company.is_active = False
        await self.session.commit()
