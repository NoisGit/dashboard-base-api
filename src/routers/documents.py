"""Documents router module for Coredeck API."""

from typing import Optional

from fastapi import APIRouter, Depends, status
from fastapi_pagination import Page, Params

from src.auth.permissions import RoleChecker
from src.core.enums import UserRole
from src.dependencies import get_document_service
from src.schemas import (
    DocumentCreateRequest,
    DocumentUpdateRequest,
    DocumentResponse,
    DocumentDownloadResponse,
    EmptyResponse,
)
from src.services.document_service import DocumentService

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
)


@router.get(
    "/all",
    response_model=Page[DocumentResponse],
)
async def list_all_documents(
    params: Params = Depends(),
    company_id: Optional[int] = None,
    search: Optional[str] = None,
    service: DocumentService = Depends(get_document_service),
    _=Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
            ],
        ),
    ),
) -> Page[DocumentResponse]:
    """List documents"""
    documents = await service.list_documents(
        params=params,
        company_id=company_id,
        search=search,
    )
    return documents


@router.get(
    "/me",
    response_model=Page[DocumentResponse],
)
async def list_my_company_documents(
    params: Params = Depends(),
    search: Optional[str] = None,
    service: DocumentService = Depends(get_document_service),
    user_id: int = Depends(
        RoleChecker(
            [
                UserRole.ADMIN,
                UserRole.SUBADMIN,
            ],
        ),
    ),
) -> Page[DocumentResponse]:
    """List documents"""
    documents = await service.list_my_company_documents(
        user_id=user_id,
        params=params,
        search=search,
    )
    return documents


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
)
async def get_document_detail(
    document_id: int,
    service: DocumentService = Depends(get_document_service),
    user_id: int = Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
                UserRole.ADMIN,
                UserRole.SUBADMIN,
            ],
        ),
    ),
) -> DocumentResponse:
    """Get a single document by ID"""
    document = await service.get_document_detail(
        user_id=user_id,
        document_id=document_id,
    )
    return document


@router.get(
    "/{document_id}/download",
    response_model=DocumentDownloadResponse,
)
async def download_document(
    document_id: int,
    service: DocumentService = Depends(get_document_service),
    user_id: int = Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
                UserRole.ADMIN,
                UserRole.SUBADMIN,
            ],
        ),
    ),
) -> DocumentDownloadResponse:
    """Download document"""
    result = await service.get_document_download_url(
        user_id=user_id,
        document_id=document_id,
    )
    return result


@router.post(
    "/",
    response_model=EmptyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_document(
    payload: DocumentCreateRequest,
    service: DocumentService = Depends(get_document_service),
    requester_id: int = Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
            ],
        ),
    ),
) -> EmptyResponse:
    """Create a new document"""
    result = await service.create_document(
        user_id=requester_id,
        payload=payload,
    )
    return result


@router.put(
    "/{document_id}",
    response_model=EmptyResponse,
)
async def update_document(
    document_id: int,
    payload: DocumentUpdateRequest,
    service: DocumentService = Depends(get_document_service),
    _=Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
            ],
        ),
    ),
) -> EmptyResponse:
    """Update an existing document"""
    result = await service.update_document(
        document_id=document_id,
        payload=payload,
    )
    return result


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_document(
    document_id: int,
    service: DocumentService = Depends(get_document_service),
    _=Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
            ],
        ),
    ),
):
    """Hard delete a document"""
    await service.delete_document(
        document_id=document_id,
    )
