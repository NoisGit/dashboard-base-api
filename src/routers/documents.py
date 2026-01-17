"""Documents router module for Sentinel Enterprise API."""

from typing import Optional, Union

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from fastapi_pagination import Page, Params

from src.auth.permissions import RoleChecker
from src.core.enums import UserRole
from src.dependencies import get_document_service
from src.schemas import (
    DocumentCreateRequest,
    DocumentUpdateRequest,
    DocumentResponse,
    DocumentDownloadResponse,
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
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_document(
    company_id: int = Form(...),
    name: str = Form(...),
    comment: str = Form(""),
    file: UploadFile = File(...),
    service: DocumentService = Depends(get_document_service),
    requester_id: int = Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
            ],
        ),
    ),
) -> DocumentResponse:
    """Create a new document"""
    payload = DocumentCreateRequest(
        company_id=company_id,
        name=name.strip(),
        comment=comment.strip() or None,
    )

    document = await service.create_document(
        user_id=requester_id,
        payload=payload,
        file=file,
    )
    return document


@router.put(
    "/{document_id}",
    response_model=DocumentResponse,
)
async def update_document(
    document_id: int,
    name: Optional[str] = Form(None),
    comment: Optional[str] = Form(None),
    file: Optional[Union[UploadFile, str]] = File(None),
    service: DocumentService = Depends(get_document_service),
    _=Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
            ],
        ),
    ),
) -> DocumentResponse:
    """Update an existing document"""
    normalized_name = name.strip() if name is not None else None
    normalized_comment = comment.strip() if comment is not None else None

    upload_file: Optional[UploadFile] = None
    if isinstance(file, UploadFile) and file.filename:
        upload_file = file

    payload = DocumentUpdateRequest(
        name=normalized_name,
        comment=normalized_comment,
    )

    document = await service.update_document(
        document_id=document_id,
        payload=payload,
        file=upload_file,
    )
    return document


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
