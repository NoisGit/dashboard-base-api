from __future__ import annotations

"""
Companies router for Sentinel Enterprise API.

First iteration of the Company CRUD:

- JWT-based security (access token required).
- Basic listing of active companies.
- Company creation restricted to superadmin.
- Initial role handling based on JWT payload.

TODO (next steps):
- Restrict visibility by company_staff for admin/subadmin/janitor/client.
- Implement PUT /api/company/{id}.
- Implement DELETE /api/company/{id} with soft delete (is_active = False).
- Improve error handling and add tests.
"""

from typing import List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import SQLModel, Field, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Company  # CompanyStaff will be used in the next iteration
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


class CompanyBase(SQLModel):
    """
    Base data for Company.

    Mapping vs functional description:
    - Name   -> name
    - RUT    -> id_number
    - Activity -> activity
    """
    name: str = Field(max_length=100)
    activity: str | None = Field(default=None, max_length=100)
    id_number: str | None = Field(default=None, max_length=50)  # RUT / id_number
    logo: str | None = Field(default=None, max_length=255)
    type_document: str | None = Field(default=None, max_length=30)


class CompanyCreate(CompanyBase):
    """Payload used to create a company (first version)."""
    pass


class CompanyRead(CompanyBase):
    id: int
    created_by: int
    is_active: bool

    class Config:
        from_attributes = True


# -----------------------------
# Basic auth helpers
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


def ensure_superadmin(current_user: Dict[str, Any]) -> None:
    role = _get_role(current_user)
    if role != ROLE_SUPERADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superadmin can perform this action.",
        )


# -----------------------------
# Endpoints (first iteration)
# -----------------------------


@router.get("/companies", response_model=List[CompanyRead])
async def list_companies(
    session: AsyncSession = Depends(get_session),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> list[CompanyRead]:
    """
    List active companies.

    First iteration:
    - SUPERADMIN: lists all active companies.
    - Other roles: same behavior for now (TODO: restrict by company_staff).

    TODO:
    - Filter by companies associated to the user via company_staff for
      admin / subadmin / janitor / client roles.
    """
    ensure_authenticated(current_user)
    _ = _get_role(current_user)
    _ = _get_user_id(current_user)  # will be used in the next iteration

    # For now, all authenticated roles see the same list of active companies.
    # In the next iteration this will be restricted based on company_staff.
    stmt = select(Company).where(Company.is_active == True)

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
    Create a company.

    First iteration:
    - Only SUPERADMIN can create companies.

    TODO:
    - Revisit if "admin company" should be allowed to create child companies
      or if this stays exclusive to superadmin.
    """
    ensure_authenticated(current_user)
    ensure_superadmin(current_user)

    user_id = _get_user_id(current_user)

    company = Company(
        name=payload.name,
        activity=payload.activity,
        id_number=payload.id_number,
        logo=payload.logo,
        type_document=payload.type_document,
        created_by=user_id,
        # is_active = True by default at the model level
    )
    session.add(company)
    await session.commit()
    await session.refresh(company)
    return company
