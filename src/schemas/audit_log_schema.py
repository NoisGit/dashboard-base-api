"""Audit log schema definitions."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from src.core.enums import AuditAction, TableName


class AuditLogRequest(BaseModel):
    """Schema for audit log request data."""
    user_id: int
    action: AuditAction
    table_name: Optional[TableName] = None
    record_id: Optional[int] = None
    description: Optional[str] = None


class AuditLogResponse(BaseModel):
    """Schema for audit log response data."""
    id: int
    user_name: str
    action: AuditAction
    table_name: Optional[TableName] = None
    record_id: Optional[int] = None
    description: Optional[str] = None
    created_at: datetime
