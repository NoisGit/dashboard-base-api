"""Company service module for the Sentinel Enterprise API."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.core.enums import UserRole
from src.models import Company, CompanyStaff, User

from src.schemas import (
    CompanyCreateRequest,
    CompanyUpdateRequest,
)

# pylint: disable=no-member, singleton-comparison
# noqa: E712

# Role sets derived directly from the UserRole enum
ROLES_CAN_VIEW_ASSOCIATED = {
    UserRole.SUPERADMIN.value,
    UserRole.ADMIN.value,
    UserRole.SUBADMIN.value,
    UserRole.JANITOR.value,
    UserRole.CLIENT.value,
}

ROLES_CAN_EDIT_COMPANY = {
    UserRole.SUPERADMIN.value,
    UserRole.ADMIN.value,
}

ROLES_CAN_CREATE_DELETE_COMPANY = {
    UserRole.SUPERADMIN.value,
}


class CompanyService:
    """Application service for company-related operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ---------- RBAC helpers ----------

    def _get_role(self, current_user: Dict[str, Any]) -> str:
        role = current_user.get("role")
        if role is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Role not found in token payload.",
            )
        return role

    def _get_user_id(self, current_user: Dict[str, Any]) -> int:
        user_id = current_user.get("user_id")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="user_id not found in token payload.",
            )
        return int(user_id)

    def _ensure_authenticated(self, current_user: Dict[str, Any]) -> None:
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required.",
            )

    def _ensure_can_view_companies(self, current_user: Dict[str, Any]) -> None:
        role = self._get_role(current_user)
        if role not in ROLES_CAN_VIEW_ASSOCIATED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to view companies.",
            )

    def _ensure_can_edit_companies(self, current_user: Dict[str, Any]) -> None:
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
        role = self._get_role(current_user)
        if role == UserRole.SUPERADMIN.value:
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
        return await self.session.get(Company, company_id)

    # ---------- Public methods ----------

    async def list_companies(
        self,
        current_user: Dict[str, Any],
    ) -> List[Company]:
        """List active companies visible for the current user."""
        self._ensure_authenticated(current_user)
        self._ensure_can_view_companies(current_user)

        role = self._get_role(current_user)
        user_id = self._get_user_id(current_user)

        if role == UserRole.SUPERADMIN.value:
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
        payload: CompanyCreateRequest,
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
        payload: CompanyUpdateRequest,
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
        """Soft delete a company by setting is_active = False."""
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

    async def assign_user_to_company(
        self,
        current_user: Dict[str, Any],
        company_id: int,
        user_id: int,
    ) -> CompanyStaff:
        """
        Assign an existing user to a company via CompanyStaff.

        Rules:
        - Only roles allowed to edit companies can assign users.
        - ADMIN must be linked to the target company (SUPERADMIN bypasses).
        - The user must exist and be active.
        - The user must not already belong to another company (1:1 rule).
        """
        self._ensure_authenticated(current_user)
        self._ensure_can_edit_companies(current_user)

        company = await self._get_company_by_id(company_id)
        if not company or not company.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found.",
            )

        await self._ensure_user_linked_to_company(company_id, current_user)

        user_stmt = select(User).where(User.id == user_id)
        user_result = await self.session.execute(user_stmt)
        user = user_result.scalars().first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        link_stmt = select(CompanyStaff).where(CompanyStaff.user_id == user_id)
        link_result = await self.session.execute(link_stmt)
        existing_link = link_result.scalars().first()

        if existing_link:
            if existing_link.company_id == company_id:
                return existing_link

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User is already assigned to another company.",
            )

        creator_id = self._get_user_id(current_user)
        new_link = CompanyStaff(
            user_id=user_id,
            company_id=company_id,
            created_by=creator_id,
        )

        self.session.add(new_link)
        await self.session.commit()
        await self.session.refresh(new_link)
        return new_link
