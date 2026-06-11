"""Company-related Pydantic schemas for the Locentr API."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from .base_schemas import BaseResponse


class CompanyCreateRequest(BaseModel):
    """Payload for creating a company."""
    name: str = Field(min_length=2, max_length=100)
    activity: Optional[str] = Field(default=None, max_length=100)
    id_number: str = Field(min_length=2, max_length=50)
    logo: Optional[str] = Field(default=None, max_length=255)
    type_document: str = Field(min_length=2, max_length=30)


class SubCompanyCreateRequest(BaseModel):
    """Payload for creating a sub company."""
    name: str = Field(min_length=2, max_length=100)
    activity: Optional[str] = None
    id_number: str = Field(min_length=2, max_length=50)
    parent_company_id: Optional[int] = None
    logo: Optional[str] = None
    type_document: str = Field(min_length=2, max_length=30)


class CompanyUpdateRequest(BaseModel):
    """Payload for updating a company."""
    name: Optional[str] = None
    activity: Optional[str] = None
    id_number: Optional[str] = None
    logo: Optional[str] = None
    type_document: Optional[str] = None


class CompanyResponse(BaseResponse):
    """Company response schema"""
    id: int
    name: str
    activity: Optional[str] = None
    id_number: Optional[str] = None
    logo: Optional[str] = None
    type_document: Optional[str] = None
    is_active: bool
    parent_company_id: Optional[int] = None
    created_by: int
    created_at: Optional[datetime] = None


class CompanyAssignUserRequest(BaseModel):
    """Payload for assigning an existing user to a company."""
    user_id: int


class CompanyUserAssignmentResponse(BaseModel):
    """User–company assignment representation."""
    company_id: int
    user_id: int


__all__ = [
    "CompanyCreateRequest",
    "SubCompanyCreateRequest",
    "CompanyUpdateRequest",
    "CompanyResponse",
    "CompanyAssignUserRequest",
    "CompanyUserAssignmentResponse",
]
