"""Pydantic schemas for storage requests and responses."""

from pydantic import BaseModel


class StorageUploadRequest(BaseModel):
    """Schema for upload request data."""
    container_name: str
    file_extension: str
    content_type: str


class StorageUpdateRequest(BaseModel):
    """Schema for update request data."""
    old_blob_url: str
    file_extension: str
    content_type: str


class StorageDeleteRequest(BaseModel):
    """Schema for delete request data."""
    blob_url: str


class StorageResponse(BaseModel):
    """Schema for response data."""
    blob_url: str
    blob_name: str


class StorageUpdateResponse(BaseModel):
    """Schema for response data."""
    delete_url: str
    new_blob_name: str
    new_blob_url: str


class StorageDeleteResponse(BaseModel):
    """Schema for response data."""
    blob_url: str


__all__ = [
    "StorageUploadRequest",
    "StorageUpdateRequest",
    "StorageDeleteRequest",
    "StorageResponse",
    "StorageUpdateResponse",
    "StorageDeleteResponse",
]
