"""Document service module for the Sentinel Enterprise API."""

# pylint: disable=no-member, singleton-comparison

import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional, cast

from fastapi import HTTPException, UploadFile, status
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.api.error import AzureServiceError
from src.config.config import settings
from src.core.enums import UserRole
from src.models import Company, CompanyStaff, Document
from src.schemas import (
    DocumentCreateRequest,
    DocumentDownloadResponse,
    DocumentResponse,
    DocumentUpdateRequest,
)
from src.services.azure_service import AzureService
from src.services.user_service import UserService


DEFAULT_ALLOWED_EXTENSIONS = [".pdf", ".png", ".jpg", ".jpeg"]
DEFAULT_MAX_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
DOCUMENTS_CONTAINER_NAME = "documents"


class DocumentService:
    """Service for document operations."""

    def __init__(
        self,
        session: AsyncSession,
        user_service: UserService,
        azure_service: AzureService,
    ) -> None:
        self.session = session
        self.user_service = user_service
        self.azure_service = azure_service

    async def _get_document_by_id(
        self,
        document_id: int,
    ) -> Optional[Document]:
        return await self.session.get(Document, document_id)

    async def _get_user_company_id(
        self,
        user_id: int,
    ) -> Optional[int]:
        stmt = select(CompanyStaff.company_id).where(
            CompanyStaff.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        row = result.first()
        return row[0] if row else None

    async def _ensure_can_access_document(
        self,
        user_id: int,
        document: Document,
    ) -> None:
        user = await self.user_service.get_user_by_id(user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        if user.role == UserRole.SUPERADMIN:
            return

        company_id = await self._get_user_company_id(user_id)
        if company_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is not assigned to a company.",
            )

        if document.company_id != company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this document.",
            )

    def _get_allowed_extensions(self) -> List[str]:
        allowed = getattr(settings, "DOCUMENTS_ALLOWED_EXTENSIONS", None)
        if not allowed:
            return DEFAULT_ALLOWED_EXTENSIONS

        if isinstance(allowed, str):
            parts = [p.strip() for p in allowed.split(",")]
            return [p if p.startswith(".") else f".{p}" for p in parts if p]

        return list(allowed)

    def _get_max_size_bytes(self) -> int:
        max_size = getattr(
            settings, "DOCUMENTS_MAX_SIZE_BYTES", DEFAULT_MAX_SIZE_BYTES
        )
        return int(max_size)

    def _validate_file(
        self,
        file: UploadFile,
        content: bytes,
    ) -> str:
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File name is required.",
            )

        ext = Path(file.filename).suffix.lower()
        allowed_extensions = {e.lower()
                              for e in self._get_allowed_extensions()}

        if ext not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File extension is not allowed.",
            )

        max_size = self._get_max_size_bytes()
        if len(content) > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size exceeds the maximum allowed limit.",
            )

        return ext

    def _build_blob_name(
        self,
        company_id: int,
        ext: str,
    ) -> str:
        unique = uuid.uuid4().hex
        timestamp = int(datetime.now().timestamp())
        return f"company_{company_id}/{unique}_{timestamp}{ext}"

    def _to_document_response(self, doc: Document) -> DocumentResponse:
        url = self.azure_service.generate_read_sas_url(
            container_name=DOCUMENTS_CONTAINER_NAME,
            blob_name=doc.blob_name,
        )

        return DocumentResponse(
            id=doc.id,
            company_id=doc.company_id,
            user_id=doc.user_id,
            name=doc.name,
            file_name=doc.file_name,
            blob_name=doc.blob_name,
            url=url,
            comment=doc.comment,
            content_type=doc.content_type,
            size_bytes=doc.size_bytes,
            created_by=doc.created_by,
            created_at=doc.created_at,
        )

    async def list_documents(
        self,
        params: Params,
        company_id: Optional[int],
        search: Optional[str],
    ) -> Page[DocumentResponse]:
        """List documents with optional filters (SUPERADMIN scope)."""
        stmt = select(Document)

        if company_id is not None:
            stmt = stmt.where(Document.company_id == company_id)

        if search:
            like_pattern = f"%{search}%"
            stmt = stmt.where(
                (Document.name.ilike(like_pattern))
                | (Document.file_name.ilike(like_pattern)),
            )

        return await paginate(
            self.session,
            stmt,
            params,
            transformer=lambda items: [
                self._to_document_response(doc)
                for doc in cast(List[Document], items)
            ],
        )

    async def list_my_company_documents(
        self,
        user_id: int,
        params: Params,
        search: Optional[str],
    ) -> Page[DocumentResponse]:
        """List documents for the current user's company."""
        company_id = await self._get_user_company_id(user_id)
        if company_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is not assigned to a company.",
            )

        stmt = select(Document).where(
            Document.company_id == company_id,
        )

        if search:
            like_pattern = f"%{search}%"
            stmt = stmt.where(
                (Document.name.ilike(like_pattern))
                | (Document.file_name.ilike(like_pattern)),
            )

        return await paginate(
            self.session,
            stmt,
            params,
            transformer=lambda items: [
                self._to_document_response(doc)
                for doc in cast(List[Document], items)
            ],
        )

    async def get_document_detail(
        self,
        user_id: int,
        document_id: int,
    ) -> DocumentResponse:
        """Get a single document by ID."""
        document = await self._get_document_by_id(document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found.",
            )

        await self._ensure_can_access_document(
            user_id=user_id,
            document=document,
        )

        return self._to_document_response(document)

    async def get_document_download_url(
        self,
        user_id: int,
        document_id: int,
    ) -> DocumentDownloadResponse:
        """Generate a read URL for a document."""
        document = await self._get_document_by_id(document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found.",
            )

        await self._ensure_can_access_document(
            user_id=user_id,
            document=document,
        )

        url = self.azure_service.generate_read_sas_url(
            container_name=DOCUMENTS_CONTAINER_NAME,
            blob_name=document.blob_name,
        )

        return DocumentDownloadResponse(url=url)

    async def create_document(
        self,
        user_id: int,
        payload: DocumentCreateRequest,
        file: UploadFile,
    ) -> DocumentResponse:
        """Create a new document and upload its blob to Azure."""
        company = await self.session.get(Company, payload.company_id)
        if not company or not company.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found.",
            )

        name = payload.name.strip()
        if not name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document name is required.",
            )

        comment = payload.comment.strip() if payload.comment else None
        comment = comment or None

        content = await file.read()
        ext = self._validate_file(file=file, content=content)

        blob_name = self._build_blob_name(
            company_id=payload.company_id,
            ext=ext,
        )

        try:
            self.azure_service.upload_blob(
                container_name=DOCUMENTS_CONTAINER_NAME,
                blob_name=blob_name,
                content=content,
                content_type=file.content_type or "application/octet-stream",
            )
        except AzureServiceError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload document to Azure.",
            ) from e

        document = Document(
            company_id=payload.company_id,
            user_id=user_id,
            name=name,
            comment=comment,
            file_name=file.filename,
            blob_name=blob_name,
            content_type=file.content_type,
            size_bytes=len(content),
            created_by=user_id,
            created_at=datetime.now(),
        )

        self.session.add(document)
        await self.session.commit()
        await self.session.refresh(document)

        return self._to_document_response(document)

    async def update_document(
        self,
        document_id: int,
        payload: DocumentUpdateRequest,
        file: Optional[UploadFile],
    ) -> DocumentResponse:
        """Update document metadata and optionally replace the file."""
        document = await self._get_document_by_id(document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found.",
            )

        if payload.name is not None:
            name = payload.name.strip()
            if not name:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Document name is required.",
                )
            document.name = name

        if payload.comment is not None:
            comment = payload.comment.strip() or None
            document.comment = comment

        old_blob_name = document.blob_name

        if file is not None:
            content = await file.read()
            ext = self._validate_file(file=file, content=content)

            new_blob_name = self._build_blob_name(
                company_id=document.company_id,
                ext=ext,
            )

            try:
                self.azure_service.upload_blob(
                    container_name=DOCUMENTS_CONTAINER_NAME,
                    blob_name=new_blob_name,
                    content=content,
                    content_type=file.content_type or "application/octet-stream",
                )
            except AzureServiceError as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to upload document to Azure.",
                ) from e

            document.file_name = file.filename
            document.blob_name = new_blob_name
            document.content_type = file.content_type
            document.size_bytes = len(content)

        await self.session.commit()
        await self.session.refresh(document)

        if file is not None:
            try:
                self.azure_service.delete_blob(
                    container_name=DOCUMENTS_CONTAINER_NAME,
                    blob_name=old_blob_name,
                )
            except AzureServiceError:
                pass

        return self._to_document_response(document)

    async def delete_document(
        self,
        document_id: int,
    ) -> None:
        """Hard delete a document and remove its blob from Azure."""
        document = await self._get_document_by_id(document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found.",
            )

        try:
            self.azure_service.delete_blob(
                container_name=DOCUMENTS_CONTAINER_NAME,
                blob_name=document.blob_name,
            )
        except AzureServiceError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete document from Azure.",
            ) from e

        await self.session.delete(document)
        await self.session.commit()
