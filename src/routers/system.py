"""System Router"""
from fastapi import APIRouter, Depends

from src.auth.permissions import RoleChecker
from src.core.enums import UserRole
from src.dependencies import get_system_service
from src.services.system_service import SystemService
from src.schemas import (
    SystemCountersResponse,
    SystemStatsResponse,
    MonthlyIncomeResponse,
    DetailAdminsResponse,
)

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/stats", response_model=SystemStatsResponse)
async def get_system_stats(
    service: SystemService = Depends(get_system_service),
    _=Depends(RoleChecker([UserRole.SUPERADMIN]))
) -> SystemStatsResponse:
    """Retrieve system statistics."""
    system_stats = await service.get_system_stats()
    return system_stats

# FOR TESTING PURPOSES ONLY


@router.get("/counter-stats", response_model=SystemCountersResponse)
async def get_counter_system_stats(
    service: SystemService = Depends(get_system_service),
    _=Depends(RoleChecker([UserRole.SUPERADMIN]))
) -> SystemCountersResponse:
    """Retrieve system statistics."""
    counter_system_stats = await service.get_system_counters()
    return counter_system_stats


# FOR TESTING PURPOSES ONLY
@router.get("/income-by-month", response_model=MonthlyIncomeResponse)
async def get_income_by_month(
    service: SystemService = Depends(get_system_service),
    _=Depends(RoleChecker([UserRole.SUPERADMIN]))
) -> MonthlyIncomeResponse:
    """Retrieve system income by month."""
    income_by_month = await service.get_system_detail_income_by_month()
    return income_by_month

# FOR TESTING PURPOSES ONLY


@router.get("/detail-admins", response_model=DetailAdminsResponse)
async def get_detail_admins(
    service: SystemService = Depends(get_system_service),
    _=Depends(RoleChecker([UserRole.SUPERADMIN]))
) -> DetailAdminsResponse:
    """Retrieve system admin details."""
    detail_admins = await service.get_detail_admins()
    return detail_admins
