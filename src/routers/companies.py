"""Companies router module for Sentinel Enterprise API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from fastapi_pagination import Page, paginate

from src.auth.utils import get_user_data_from_token
from src.auth.permissions import RoleChecker
from src.core.enums import UserRole
from src.dependencies import get_company_service
from src.schemas import (
    CompanyCreateRequest,
    CompanyUpdateRequest,
    CompanyResponse,
    CompanyAssignUserRequest,
    CompanyUserAssignmentResponse,
)
from src.services.company_service import CompanyService

router = APIRouter(
    prefix="/companies",
    tags=["companies"],
)


@router.get(
    "/",
    response_model=Page[CompanyResponse],
)
async def list_companies(
    service: CompanyService = Depends(get_company_service),
    current_user_data: tuple[int, UserRole] = Depends(
        get_user_data_from_token),
) -> Page[CompanyResponse]:
    """List active companies for the current user."""
    user_id, role = current_user_data

    companies = await service.list_companies(
        user_id=user_id,
        role=role,
    )
    return paginate(companies)


@router.get(
    "/{company_id}",
    response_model=CompanyResponse,
)
async def get_company_detail(
    company_id: int,
    service: CompanyService = Depends(get_company_service),
    current_user_data: tuple[int, UserRole] = Depends(
        get_user_data_from_token),
) -> CompanyResponse:
    """Get a single active company by ID."""
    user_id, role = current_user_data

    company = await service.get_company_detail(
        user_id=user_id,
        role=role,
        company_id=company_id,
    )
    return company


@router.post(
    "/",
    response_model=CompanyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_company(
    payload: CompanyCreateRequest,
    service: CompanyService = Depends(get_company_service),
    current_user_data: tuple[int, UserRole] = Depends(
        RoleChecker([UserRole.SUPERADMIN]),
    ),
) -> CompanyResponse:
    """Create a new company."""
    requester_id, _ = current_user_data

    company = await service.create_company(
        requester_id=requester_id,
        payload=payload,
    )
    return company


@router.put(
    "/{company_id}",
    response_model=CompanyResponse,
)
async def update_company(
    company_id: int,
    payload: CompanyUpdateRequest,
    service: CompanyService = Depends(get_company_service),
    current_user_data: tuple[int, UserRole] = Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
                UserRole.ADMIN,
            ],
        ),
    ),
) -> CompanyResponse:
    """Update an existing company."""
    requester_id, requester_role = current_user_data

    company = await service.update_company(
        requester_id=requester_id,
        requester_role=requester_role,
        company_id=company_id,
        payload=payload,
    )
    return company


@router.delete(
    "/{company_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_company(
    company_id: int,
    service: CompanyService = Depends(get_company_service),
    _: tuple[int, UserRole] = Depends(
        RoleChecker([UserRole.SUPERADMIN]),
    ),
):
    """Soft delete a company by setting is_active = False."""
    await service.soft_delete_company(
        company_id=company_id,
    )


@router.post(
    "/{company_id}/users",
    response_model=CompanyUserAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def assign_user_to_company(
    company_id: int,
    payload: CompanyAssignUserRequest,
    service: CompanyService = Depends(get_company_service),
    current_user_data: tuple[int, UserRole] = Depends(
        RoleChecker([UserRole.SUPERADMIN, UserRole.ADMIN]),
    ),
) -> CompanyUserAssignmentResponse:
    """Assign an existing user to a company."""
    requester_id, requester_role = current_user_data

    await service.assign_user_to_company(
        requester_id=requester_id,
        requester_role=requester_role,
        company_id=company_id,
        user_id=payload.user_id,
    )

    return CompanyUserAssignmentResponse(
        company_id=company_id,
        user_id=payload.user_id,
    )
