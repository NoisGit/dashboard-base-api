"""Dashboard Router"""
from fastapi import APIRouter, Depends

from src.auth.permissions import RoleChecker
from src.core.enums import UserRole
from src.dependencies import get_dashboard_service
from src.services.dashboard_service import DashboardService
from src.schemas import (
    DashboardStatsResponse,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/location/{location_id}", response_model=DashboardStatsResponse)
async def dashboard_stats(
    location_id: int,
    service: DashboardService = Depends(get_dashboard_service),
    user_id=Depends(RoleChecker([
        UserRole.SUPERADMIN,
        UserRole.ADMIN,
        UserRole.CLIENT,
    ])),
) -> DashboardStatsResponse:
    """Retrieve system statistics."""
    system_stats = await service.get_dashboard_stats(user_id, location_id)
    return system_stats
