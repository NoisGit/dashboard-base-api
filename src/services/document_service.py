"""Document service module for the Coredeck API."""

# pylint: disable=no-member, singleton-comparison

from datetime import datetime
from pathlib import Path
from typing import List, Optional, cast

from fastapi import HTTPException, status
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.config.config import settings
from src.core.enums import UserRole
from src.models import Company, CompanyStaff, Document
from src.schemas import (
    DocumentCreateRequest,
    DocumentDownloadResponse,
    DocumentResponse,
    DocumentUpdateRequest,
    EmptyResponse,
)
from src.services.storage_service import StorageService
from src.services.user_service import UserService


DEFAULT_ALLOWED_EXTENSIONS = [".pdf", ".png", ".jpg", ".jpeg"]
DEFAULT_MAX_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


class DocumentService:
    """Service for document operations."""

    def __init__(
        self,
        session: AsyncSession,
        user_service: UserService,
        storage_service: StorageService,
    ) -> None:
        self.session = session
        self.user_service = user_service
        self.storage_service = storage_service

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

    def _normalize_optional_str(self, value: Optional[str]) -> Optional[str]:
        """Treat empty or 'string' values as None (Swagger defaults)."""
        if value is None:
            return None
        normalized = value.strip()
        if not normalized or normalized.lower() == "string":
            return None
        return normalized

    def _validate_metadata(
        self,
        file_name: str,
        size_bytes: Optional[int],
    ) -> None:
        if not file_name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="file_name is required.",
            )

        ext = Path(file_name).suffix.lower()
        allowed_extensions = {e.lower()
                              for e in self._get_allowed_extensions()}
        if ext not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File extension is not allowed.",
            )

        if size_bytes is not None:
            max_size = self._get_max_size_bytes()
            if size_bytes > max_size:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File size exceeds the maximum allowed limit.",
                )

    def _to_document_response(self, doc: Document) -> DocumentResponse:
        url = self.storage_service.generate_read_url(
            container_name="documents",
            object_name=doc.blob_name,
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

        url = self.storage_service.generate_read_url(
            container_name="documents",
            object_name=document.blob_name,
        )

        return DocumentDownloadResponse(url=url)

    async def create_document(
        self,
        user_id: int,
        payload: DocumentCreateRequest,
    ) -> EmptyResponse:
        """Create a new document record (metadata only)."""
        company = await self.session.get(Company, payload.company_id)
        if not company or not company.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found.",
            )

        name = payload.name.strip()
        if not name or name.lower() == "string":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document name is required.",
            )

        file_name = payload.file_name.strip()
        blob_name = payload.blob_name.strip()

        if not file_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="file_name is required.",
            )
        if not blob_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="blob_name is required.",
            )

        comment = payload.comment.strip() if payload.comment else None
        if comment and comment.lower() == "string":
            comment = None

        self._validate_metadata(
            file_name=file_name,
            size_bytes=payload.size_bytes,
        )

        document = Document(
            company_id=payload.company_id,
            user_id=user_id,
            name=name,
            comment=comment or None,
            file_name=file_name,
            blob_name=blob_name,
            content_type=payload.content_type,
            size_bytes=payload.size_bytes,
            created_by=user_id,
            created_at=datetime.now(),
        )

        self.session.add(document)
        await self.session.commit()
        await self.session.refresh(document)

        return EmptyResponse()

    async def update_document(
        self,
        document_id: int,
        payload: DocumentUpdateRequest,
    ) -> EmptyResponse:
        """Update document metadata (optionally replace blob metadata)."""
        document = await self._get_document_by_id(document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found.",
            )

        normalized_name = self._normalize_optional_str(payload.name)
        if normalized_name is not None:
            document.name = normalized_name

        normalized_comment = self._normalize_optional_str(payload.comment)
        if payload.comment is not None:
            document.comment = normalized_comment

        normalized_blob_name = self._normalize_optional_str(payload.blob_name)
        if normalized_blob_name is not None:
            document.blob_name = normalized_blob_name

        normalized_file_name = self._normalize_optional_str(payload.file_name)
        if normalized_file_name is not None:
            self._validate_metadata(
                file_name=normalized_file_name,
                size_bytes=payload.size_bytes
                if payload.size_bytes is not None
                else document.size_bytes,
            )
            document.file_name = normalized_file_name

        normalized_content_type = self._normalize_optional_str(
            payload.content_type)
        if payload.content_type is not None:
            document.content_type = normalized_content_type

        if payload.size_bytes is not None:
            document.size_bytes = payload.size_bytes

        await self.session.commit()

        return EmptyResponse()

    async def delete_document(
        self,
        document_id: int,
    ) -> None:
        """Hard delete a document record (does not delete blob)."""
        document = await self._get_document_by_id(document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found.",
            )

        await self.session.delete(document)
        await self.session.commit()
