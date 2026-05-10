"""Pydantic schemas for storage requests and responses."""

from pydantic import BaseModel


class StorageUploadRequest(BaseModel):
    """Schema for upload request data."""
    container_name: str
    file_extension: str
    content_type: str


class StorageUpdateRequest(BaseModel):
    """Schema for update request data."""
    old_object_url: str
    file_extension: str
    content_type: str


class StorageDeleteRequest(BaseModel):
    """Schema for delete request data."""
    object_url: str


class StorageResponse(BaseModel):
    """Schema for response data."""
    object_url: str
    object_name: str


class StorageUpdateResponse(BaseModel):
    """Schema for response data."""
    delete_url: str
    new_object_name: str
    new_object_url: str


class StorageDeleteResponse(BaseModel):
    """Schema for response data."""
    object_url: str


__all__ = [
    "StorageUploadRequest",
    "StorageUpdateRequest",
    "StorageDeleteRequest",
    "StorageResponse",
    "StorageUpdateResponse",
    "StorageDeleteResponse",
]
