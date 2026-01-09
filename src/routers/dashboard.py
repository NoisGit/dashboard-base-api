"""Dashboard Router"""
from fastapi import APIRouter, Depends

from src.auth.permissions import RoleChecker
from src.core.enums import UserRole
from src.dependencies import get_dashboard_service
from src.services.dashboard_service import DashboardService
from src.schemas import (
    KpisResponse,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/{location_id}/kpis", response_model=KpisResponse)
async def get_dashboard_stats(
    location_id: int,
    service: DashboardService = Depends(get_dashboard_service),
    user_id=Depends(RoleChecker([
        UserRole.CLIENT,
        UserRole.SUBADMIN,
        UserRole.ADMIN,
        UserRole.SUPERADMIN
    ])),
) -> KpisResponse:
    """Retrieve system statistics."""
    system_stats = await service.get_kpis(user_id, location_id)
    return system_stats
