"""Document Pydantic schemas for the Sentinel Enterprise API."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from .base_schemas import BaseResponse


class DocumentCreateRequest(BaseModel):
    """Schema for creating a document record (metadata only)."""

    company_id: int
    name: str
    file_name: str
    blob_name: str
    content_type: Optional[str] = None
    size_bytes: Optional[int] = None
    comment: Optional[str] = None


class DocumentUpdateRequest(BaseModel):
    """Schema for updating a document metadata."""

    name: Optional[str] = None
    comment: Optional[str] = None
    file_name: Optional[str] = None
    blob_name: Optional[str] = None
    content_type: Optional[str] = None
    size_bytes: Optional[int] = None


class DocumentResponse(BaseResponse):
    """Schema for document response."""

    id: int
    company_id: int
    user_id: int
    name: str
    file_name: str
    blob_name: str

    url: Optional[str] = None

    comment: Optional[str] = None
    content_type: Optional[str] = None
    size_bytes: Optional[int] = None
    created_by: int
    created_at: datetime


class DocumentDownloadResponse(BaseResponse):
    """Schema for document download response."""

    url: str
