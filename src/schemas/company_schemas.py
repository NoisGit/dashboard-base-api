"""Company-related Pydantic schemas for the Sentinel Enterprise API."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CompanyCreateRequest(BaseModel):
    """Schema for creating a company."""
    name: str
    activity: Optional[str] = None
    id_number: Optional[str] = None
    logo: Optional[str] = None
    type_document: Optional[str] = None


class CompanyUpdateRequest(BaseModel):
    """Schema for updating a company."""
    name: Optional[str] = None
    activity: Optional[str] = None
    id_number: Optional[str] = None
    logo: Optional[str] = None
    type_document: Optional[str] = None


class CompanyResponse(BaseModel):
    """Schema for company response (without internal details)."""
    id: int
    name: str
    activity: Optional[str] = None
    id_number: Optional[str] = None
    logo: Optional[str] = None
    type_document: Optional[str] = None
    is_active: bool
    created_by: int
    created_at: Optional[datetime] = None

    class Config:
        """Pydantic config to allow ORM objects."""
        from_attributes = True


class CompanyAssignUserRequest(BaseModel):
    """Schema for assigning an existing user to a company."""
    user_id: int


class CompanyUserAssignmentResponse(BaseModel):
    """Schema representing a user-company assignment."""
    company_id: int
    user_id: int


__all__ = [
    "CompanyCreateRequest",
    "CompanyUpdateRequest",
    "CompanyResponse",
    "CompanyAssignUserRequest",
    "CompanyUserAssignmentResponse",
]
