"""Company-related Pydantic schemas for the Coredeck API."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from .base_schemas import BaseResponse


class CompanyCreateRequest(BaseModel):
    """Payload for creating a company."""
    name: str
    activity: Optional[str] = None
    id_number: Optional[str] = None
    logo: Optional[str] = None
    type_document: Optional[str] = None


class SubCompanyCreateRequest(BaseModel):
    """Payload for creating a sub company."""
    name: str
    activity: Optional[str] = None
    id_number: Optional[str] = None
    parent_company_id: Optional[int] = None
    logo: Optional[str] = None
    type_document: Optional[str] = None


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
    "CompanyUpdateRequest",
    "CompanyResponse",
    "CompanyAssignUserRequest",
    "CompanyUserAssignmentResponse",
]
