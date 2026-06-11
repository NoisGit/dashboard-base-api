"""Document Pydantic schemas for the Locentr API."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from .base_schemas import BaseResponse


class DocumentCreateRequest(BaseModel):
    """Schema for creating a document record (metadata only)."""

    company_id: int = Field(gt=0)
    name: str = Field(min_length=2, max_length=160)
    file_name: str = Field(min_length=1, max_length=255)
    blob_name: str = Field(min_length=1, max_length=255)
    content_type: Optional[str] = Field(default=None, max_length=100)
    size_bytes: Optional[int] = Field(default=None, ge=0, le=10 * 1024 * 1024)
    comment: Optional[str] = Field(default=None, max_length=1000)


class DocumentUpdateRequest(BaseModel):
    """Schema for updating a document metadata."""

    name: Optional[str] = Field(default=None, min_length=2, max_length=160)
    comment: Optional[str] = Field(default=None, max_length=1000)
    file_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    blob_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    content_type: Optional[str] = Field(default=None, max_length=100)
    size_bytes: Optional[int] = Field(default=None, ge=0, le=10 * 1024 * 1024)


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
