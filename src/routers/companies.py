"""Companies router module for Coredeck API."""

from fastapi import APIRouter, Depends, status
from fastapi_pagination import Page, Params

from src.auth.permissions import RoleChecker
from src.core.enums import UserRole
from src.dependencies import get_company_service
from src.schemas import (
    EmptyResponse,
    CompanyCreateRequest,
    CompanyUpdateRequest,
    CompanyResponse,
    CompanyAssignUserRequest,
    UserCreateRequest,
    SubCompanyCreateRequest
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
    params: Params = Depends(),
    service: CompanyService = Depends(get_company_service),
    _=Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
                UserRole.ADMIN,
            ],
        ),
    ),
) -> Page[CompanyResponse]:
    """List active companies."""
    companies = await service.list_companies(params)
    return companies


@router.get(
    "/{company_id}",
    response_model=CompanyResponse,
)
async def get_company_detail(
    company_id: int,
    service: CompanyService = Depends(get_company_service),
    _=Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
                UserRole.ADMIN,
            ],
        ),
    ),
) -> CompanyResponse:
    """Get a single active company by ID."""
    company = await service.get_company_detail(
        company_id=company_id,
    )
    return company


@router.post(
    "/",
    response_model=EmptyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_company(
    payload: CompanyCreateRequest,
    service: CompanyService = Depends(get_company_service),
    user_id=Depends(
        RoleChecker([UserRole.SUPERADMIN]),
    ),
) -> EmptyResponse:
    """Create a new company."""

    return await service.create_company(
        user_id,
        payload,
    )


@router.post(
    "/subcompany",
    response_model=EmptyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_subcompany(
    payload: SubCompanyCreateRequest,
    service: CompanyService = Depends(get_company_service),
    user_id=Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
                UserRole.ADMIN,
            ],
        ),
    ),
) -> EmptyResponse:
    """Create a new sub company."""

    return await service.create_subcompany(
        user_id,
        payload,
    )


@router.put(
    "/{company_id}",
    response_model=EmptyResponse,
)
async def update_company(
    company_id: int,
    payload: CompanyUpdateRequest,
    service: CompanyService = Depends(get_company_service),
    _=Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
                UserRole.ADMIN,
            ],
        ),
    ),
) -> EmptyResponse:
    """Update an existing company."""
    return await service.update_company(
        company_id=company_id,
        payload=payload,
    )


@router.delete(
    "/{company_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_company(
    company_id: int,
    service: CompanyService = Depends(get_company_service),
    _=Depends(RoleChecker([UserRole.SUPERADMIN])),
):
    """Soft delete a company by setting is_active = False."""
    await service.soft_delete_company(
        company_id=company_id,
    )


@router.post(
    "/{company_id}/users",
    response_model=EmptyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def assign_user_to_company(
    company_id: int,
    payload: CompanyAssignUserRequest,
    service: CompanyService = Depends(get_company_service),
    user_id=Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
                UserRole.ADMIN,
            ],
        ),
    ),
) -> EmptyResponse:
    """Assign an existing user to a company."""
    await service.assign_user_to_company(
        requester_id=user_id,
        company_id=company_id,
        user_id=payload.user_id,
    )
    return EmptyResponse()


@router.post(
    "/{company_id}/create-users",
    response_model=EmptyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_user_and_assign_to_company(
    company_id: int,
    payload: UserCreateRequest,
    service: CompanyService = Depends(get_company_service),
    user_id=Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
                UserRole.ADMIN,
            ],
        ),
    ),
) -> EmptyResponse:
    """Create user and assign an existing user to a company."""
    await service.create_user_and_assign_company(
        requester_id=user_id,
        company_id=company_id,
        payload=payload,
    )

    return EmptyResponse()
