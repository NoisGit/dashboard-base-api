"""Pydantic schemas for storage requests and responses."""

from pydantic import BaseModel, Field


class StorageUploadRequest(BaseModel):
    """Schema for upload request data."""
    container_name: str = Field(min_length=2, max_length=40)
    file_extension: str = Field(min_length=1, max_length=10)
    content_type: str = Field(min_length=3, max_length=100)


class StorageUpdateRequest(BaseModel):
    """Schema for update request data."""
    old_object_url: str = Field(min_length=10, max_length=2048)
    file_extension: str = Field(min_length=1, max_length=10)
    content_type: str = Field(min_length=3, max_length=100)


class StorageDeleteRequest(BaseModel):
    """Schema for delete request data."""
    object_url: str = Field(min_length=10, max_length=2048)


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
