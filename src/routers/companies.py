from __future__ import annotations

"""
Companies router for Sentinel Enterprise API.

Full Company CRUD behavior (backend side):

- JWT-based security (access token required).
- Role-based access control (RBAC) using JWT payload:
  * superadmin: full CRUD over all companies.
  * admin: can list and update only companies associated via company_staff.
  * subadmin / janitor / client: read-only access to associated companies.
- Soft delete:
  * DELETE /api/company/{id} sets is_active = False (no physical delete).
- Companies listing only returns active companies (is_active = True) by default.
"""

from typing import List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import SQLModel, Field, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Company, CompanyStaff
from src.database import get_session
from src.auth.utils import get_current_user

router = APIRouter(
    prefix="/api",
    tags=["companies"],
)

# -------------------------------------------------
# Roles (strings coming from the JWT payload)
# -------------------------------------------------

ROLE_SUPERADMIN = "superadmin"
ROLE_ADMIN = "admin"
ROLE_SUBADMIN = "subadmin"
ROLE_JANITOR = "janitor"      # gatekeeper / porter
ROLE_CLIENT = "client"        # end client

# Roles allowed to view associated companies
ROLES_CAN_VIEW_ASSOCIATED = {
    ROLE_SUPERADMIN,
    ROLE_ADMIN,
    ROLE_SUBADMIN,
    ROLE_JANITOR,
    ROLE_CLIENT,
}

# Roles allowed to edit companies
ROLES_CAN_EDIT_COMPANY = {
    ROLE_SUPERADMIN,
    ROLE_ADMIN,
}

# Roles allowed to create or delete companies
ROLES_CAN_CREATE_DELETE_COMPANY = {
    ROLE_SUPERADMIN,
}


# -----------------------------
# Pydantic/SQLModel schemas
# -----------------------------


class CompanyBase(SQLModel):
    """
    Base data for Company.

    Mapping vs functional description:
    - name        -> company name
    - id_number   -> RUT / tax id
    - activity    -> business activity
    """
    name: str = Field(max_length=100)
    activity: str | None = Field(default=None, max_length=100)
    id_number: str | None = Field(default=None, max_length=50)
    logo: str | None = Field(default=None, max_length=255)
    type_document: str | None = Field(default=None, max_length=30)


class CompanyCreate(CompanyBase):
    """Payload used to create a new company."""
    pass


class CompanyUpdate(SQLModel):
    """
    Payload used to update an existing company.

    All fields are optional so that we can perform partial updates using
    model_dump(exclude_unset=True).
    """
    name: str | None = Field(default=None, max_length=100)
    activity: str | None = Field(default=None, max_length=100)
    id_number: str | None = Field(default=None, max_length=50)
    logo: str | None = Field(default=None, max_length=255)
    type_document: str | None = Field(default=None, max_length=30)


class CompanyRead(CompanyBase):
    id: int
    created_by: int
    is_active: bool

    class Config:
        from_attributes = True


# -----------------------------
# Auth / RBAC helpers
# -----------------------------


def _get_role(current_user: Dict[str, Any]) -> str:
    role = current_user.get("role")
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Role not found in token payload.",
        )
    return role


def _get_user_id(current_user: Dict[str, Any]) -> int:
    user_id = current_user.get("user_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="user_id not found in token payload.",
        )
    return int(user_id)


def ensure_authenticated(current_user: Dict[str, Any]) -> None:
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )


def ensure_can_view_companies(current_user: Dict[str, Any]) -> None:
    role = _get_role(current_user)
    if role not in ROLES_CAN_VIEW_ASSOCIATED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to view companies.",
        )


def ensure_can_edit_companies(current_user: Dict[str, Any]) -> None:
    role = _get_role(current_user)
    if role not in ROLES_CAN_EDIT_COMPANY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to edit companies.",
        )


def ensure_can_create_or_delete_companies(current_user: Dict[str, Any]) -> None:
    role = _get_role(current_user)
    if role not in ROLES_CAN_CREATE_DELETE_COMPANY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to create or delete companies.",
        )


async def ensure_user_linked_to_company(
    company_id: int,
    session: AsyncSession,
    current_user: Dict[str, Any],
) -> None:
    """
    Ensure the user is linked to the given company via company_staff.

    - SUPERADMIN: bypass, always allowed.
    - ADMIN / SUBADMIN / JANITOR / CLIENT:
      must have a record in company_staff with that company_id.
    """
    role = _get_role(current_user)
    if role == ROLE_SUPERADMIN:
        return

    user_id = _get_user_id(current_user)

    stmt = (
        select(CompanyStaff)
        .where(CompanyStaff.company_id == company_id)
        .where(CompanyStaff.user_id == user_id)
    )
    result = await session.execute(stmt)
    link = result.scalars().first()

    if not link:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to access this company.",
        )


# -----------------------------
# Endpoints
# -----------------------------


@router.get("/companies", response_model=List[CompanyRead])
async def list_companies(
    session: AsyncSession = Depends(get_session),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> list[CompanyRead]:
    """
    List active companies.

    Behavior:
    - SUPERADMIN:
      * returns all companies where is_active = True.
    - ADMIN / SUBADMIN / JANITOR / CLIENT:
      * returns only active companies associated to the user via company_staff.
    """
    ensure_authenticated(current_user)
    ensure_can_view_companies(current_user)

    role = _get_role(current_user)
    user_id = _get_user_id(current_user)

    if role == ROLE_SUPERADMIN:
        stmt = select(Company).where(Company.is_active == True)
    else:
        stmt = (
            select(Company)
            .join(CompanyStaff, CompanyStaff.company_id == Company.id)
            .where(CompanyStaff.user_id == user_id)
            .where(Company.is_active == True)
        )

    result = await session.execute(stmt)
    companies = result.scalars().all()
    return companies


@router.post(
    "/company",
    response_model=CompanyRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_company(
    payload: CompanyCreate,
    session: AsyncSession = Depends(get_session),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> CompanyRead:
    """
    Create a new company.

    Behavior:
    - Only SUPERADMIN can create companies.
    """
    ensure_authenticated(current_user)
    ensure_can_create_or_delete_companies(current_user)

    user_id = _get_user_id(current_user)

    company = Company(
        name=payload.name,
        activity=payload.activity,
        id_number=payload.id_number,
        logo=payload.logo,
        type_document=payload.type_document,
        created_by=user_id,
        # is_active is True by default at the model level
    )
    session.add(company)
    await session.commit()
    await session.refresh(company)
    return company


@router.put("/company/{company_id}", response_model=CompanyRead)
async def update_company(
    company_id: int,
    payload: CompanyUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> CompanyRead:
    """
    Update an existing company.

    Behavior:
    - SUPERADMIN:
      * can update any active company.
    - ADMIN:
      * can update only active companies associated via company_staff.
    - Other roles:
      * not allowed to update companies.
    """
    ensure_authenticated(current_user)
    ensure_can_edit_companies(current_user)

    company = await session.get(Company, company_id)
    if not company or not company.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found.",
        )

    # Enforce association for all editing roles except superadmin
    await ensure_user_linked_to_company(company_id, session, current_user)

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(company, key, value)

    await session.commit()
    await session.refresh(company)
    return company


@router.delete("/company/{company_id}", status_code=status.HTTP_200_OK)
async def delete_company(
    company_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, str]:
    """
    Soft delete a company.

    Behavior:
    - Only SUPERADMIN can delete companies.
    - Soft delete only:
      * sets is_active = False.
      * does not physically remove the row to preserve referential integrity.
    """
    ensure_authenticated(current_user)
    ensure_can_create_or_delete_companies(current_user)

    company = await session.get(Company, company_id)
    if not company or not company.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found.",
        )

    company.is_active = False
    await session.commit()

    return {"detail": "Company soft-deleted successfully"}
