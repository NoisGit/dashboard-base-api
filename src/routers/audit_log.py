"""Audit Log Router"""
from fastapi_pagination import Params, Page
from fastapi import APIRouter, Depends

from src.auth.permissions import RoleChecker
from src.core.enums import UserRole
from src.dependencies import get_audit_log_service
from src.services.audit_log_service import AuditLogService
from src.schemas import AuditLogResponse

router = APIRouter(prefix="/audit-log", tags=["audit-log"])


@router.get("/", response_model=Page[AuditLogResponse])
async def get_audit_logs(
    params: Params = Depends(),
    service: AuditLogService = Depends(get_audit_log_service),
    _=Depends(RoleChecker([UserRole.SUPERADMIN]))
) -> Page[AuditLogResponse]:
    """Retrieve all audit log entries with pagination"""
    audit_logs = await service.get_all_audit_log(params)
    return audit_logs
