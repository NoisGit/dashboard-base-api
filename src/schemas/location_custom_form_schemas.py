"""Location custom form schemas for the Coredeck API."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from src.core.enums import CustomFormFieldType

from .base_schemas import BaseResponse


class LocationCustomFieldRequest(BaseModel):
    """Schema for creating a custom field for a location."""
    name: str
    field_type: CustomFormFieldType
    options: Optional[List[str]] = None
    is_required: bool = False
    display_order: int = 0
    allow_image: bool = False


class LocationCustomFieldUpdateRequest(BaseModel):
    """Schema for updating a custom field for a location."""
    name: Optional[str] = None
    field_type: Optional[CustomFormFieldType] = None
    options: Optional[List[str]] = None
    is_required: Optional[bool] = None
    display_order: Optional[int] = None
    allow_image: Optional[bool] = None


class LocationCustomFormUpsertRequest(BaseModel):
    """Schema for creating custom fields for a location."""
    fields: List[LocationCustomFieldRequest]


class LocationCustomFieldResponse(BaseResponse):
    """Schema for custom field response."""
    id: int
    form_id: int
    name: str
    field_type: CustomFormFieldType
    options: Optional[List[str]] = None
    is_required: bool
    display_order: int
    allow_image: bool = False
    is_active: bool
    created_at: datetime


class LocationCustomFormResponse(BaseResponse):
    """Schema for custom form response."""
    id: int
    location_id: int
    is_active: bool
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    fields: List[LocationCustomFieldResponse] = []


__all__ = [
    "LocationCustomFieldRequest",
    "LocationCustomFieldUpdateRequest",
    "LocationCustomFormUpsertRequest",
    "LocationCustomFieldResponse",
    "LocationCustomFormResponse",
]
