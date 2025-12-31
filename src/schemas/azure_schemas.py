"""Pydantic schemas for Azure-related requests and responses."""

from pydantic import BaseModel


class AzureUploadRequest(BaseModel):
    """Schema for upload request data."""
    container_name: str
    file_extension: str
    content_type: str


class AzureUpdateRequest(BaseModel):
    """Schema for update request data."""
    old_blob_url: str
    file_extension: str
    content_type: str


class AzureDeleteRequest(BaseModel):
    """Schema for delete request data."""
    blob_url: str


class AzureResponse(BaseModel):
    """Schema for response data."""
    blob_url: str
    blob_name: str


class AzureUpdateResponse(BaseModel):
    """Schema for response data."""
    delete_url: str
    new_blob_name: str
    new_blob_url: str


class AzureDeleteResponse(BaseModel):
    """Schema for response data."""
    blob_url: str


__all__ = [
    "AzureUploadRequest",
    "AzureUpdateRequest",
    "AzureDeleteRequest",
    "AzureResponse",
    "AzureUpdateResponse",
    "AzureDeleteResponse",
]
