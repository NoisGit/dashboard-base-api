"""System Router"""
from fastapi import APIRouter, Depends

from src.auth.permissions import RoleChecker
from src.core.enums import UserRole
from src.dependencies import get_system_service
from src.services.system_service import SystemService
from src.schemas import SystemCountersResponse

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/stats", response_model=SystemCountersResponse)
async def get_system_stats(
    service: SystemService = Depends(get_system_service),
    _=Depends(RoleChecker([UserRole.SUPERADMIN]))
) -> SystemCountersResponse:
    """Retrieve system statistics."""
    system_stats = await service.get_system_counters()
    return system_stats
