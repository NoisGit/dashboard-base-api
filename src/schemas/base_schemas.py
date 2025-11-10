"""
Base schema module.

This module provides common base models and response schemas used throughout 
the Sentinel Enterprise API. It includes standard response models for 
empty responses, success/error responses, paginated responses, and base 
configurations for Pydantic models.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class EmptyResponse(BaseModel):
    """A Pydantic model representing an empty response."""


class BaseResponse(BaseModel):
    """Base response model with common fields"""
    model_config = ConfigDict(from_attributes=True)


class PaginatedResponse(BaseModel):
    """Base paginated response"""
    total: int
    skip: int
    limit: int
    has_next: bool
    has_prev: bool


class SuccessResponse(BaseModel):
    """Success response model"""
    message: str
    timestamp: datetime = datetime.now()


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = datetime.now()
