"""Audit Log Service Module for managing audit log operations."""
from typing import cast, List
from sqlmodel import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.sqlalchemy import paginate

from src.models import AuditLog, User
from src.schemas import (
    AuditLogRequest,
    AuditLogResponse,
)


class AuditLogService:
    """Service class for audit log management operations"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def log_action(
        self,
        request: AuditLogRequest
    ):
        """Log an action performed by a user"""
        model = request.model_dump()

        audit_log_entry = AuditLog(**model)
        self.session.add(audit_log_entry)
        await self.session.commit()
        await self.session.refresh(audit_log_entry)

    async def get_all_audit_log(
        self,
        params: Params
    ) -> Page[AuditLogResponse]:
        """Retrieve all audit log entries with pagination"""
        query = \
            select(AuditLog, User) \
            .join(User, AuditLog.user_id == User.id) \
            .order_by(desc(AuditLog.created_at))

        return await paginate(
            self.session,
            query,
            params,
            transformer=lambda items: [
                AuditLogResponse(
                    id=log.id,
                    user_name=user.full_name,
                    action=log.action,
                    table_name=log.table_name,
                    record_id=log.record_id,
                    description=log.description,
                    created_at=log.created_at
                )
                for log, user in cast(List[tuple[AuditLog, User]], items)
            ]
        )
