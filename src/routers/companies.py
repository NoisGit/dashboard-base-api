"""Companies router module for Sentinel Enterprise API."""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Response, status

from src.auth.utils import get_current_user
from src.dependencies import get_company_service
from src.schemas import CompanyCreateRequest, CompanyUpdateRequest, CompanyResponse
from src.services.company_service import CompanyService

router = APIRouter(
    prefix="/companies",
    tags=["companies"],
)


@router.get("/", response_model=List[CompanyResponse])
async def list_companies(
    service: CompanyService = Depends(get_company_service),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> List[CompanyResponse]:
    """List active companies for the current user context."""
    companies = await service.list_companies(
        current_user=current_user,
    )
    return companies


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company_detail(
    company_id: int,
    service: CompanyService = Depends(get_company_service),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> CompanyResponse:
    """Get a single active company by ID."""
    company = await service.get_company_detail(
        current_user=current_user,
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
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> CompanyResponse:
    """Create a new company."""
    company = await service.create_company(
        current_user=current_user,
        payload=payload,
    )
    return company


@router.put("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: int,
    payload: CompanyUpdateRequest,
    service: CompanyService = Depends(get_company_service),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> CompanyResponse:
    """Update an existing company."""
    company = await service.update_company(
        current_user=current_user,
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
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Response:
    """Soft delete a company by setting is_active to False."""
    await service.soft_delete_company(
        current_user=current_user,
        company_id=company_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
