"""Tenant invitations and seat management."""

from typing import Optional

from fastapi import APIRouter, Depends, status

from src.auth.permissions import RoleChecker
from src.core.enums import UserRole
from src.dependencies import get_team_service
from src.schemas import (
    InvitationAcceptRequest,
    InvitationAcceptResponse,
    InvitationCreatedResponse,
    InvitationCreateRequest,
    InvitationResponse,
    SeatUsageResponse,
)
from src.services.team_service import TeamService

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("/invitations", response_model=list[InvitationResponse])
async def list_invitations(
    company_id: Optional[int] = None,
    service: TeamService = Depends(get_team_service),
    user_id: int = Depends(RoleChecker([UserRole.SUPERADMIN, UserRole.ADMIN])),
) -> list[InvitationResponse]:
    return await service.list(user_id, company_id)


@router.post(
    "/invitations",
    response_model=InvitationCreatedResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_invitation(
    payload: InvitationCreateRequest,
    service: TeamService = Depends(get_team_service),
    user_id: int = Depends(RoleChecker([UserRole.SUPERADMIN, UserRole.ADMIN])),
) -> InvitationCreatedResponse:
    return await service.create(user_id, payload)


@router.post(
    "/invitations/{invitation_id}/resend",
    response_model=InvitationCreatedResponse,
)
async def resend_invitation(
    invitation_id: int,
    service: TeamService = Depends(get_team_service),
    user_id: int = Depends(RoleChecker([UserRole.SUPERADMIN, UserRole.ADMIN])),
) -> InvitationCreatedResponse:
    return await service.resend(user_id, invitation_id)


@router.delete(
    "/invitations/{invitation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def revoke_invitation(
    invitation_id: int,
    service: TeamService = Depends(get_team_service),
    user_id: int = Depends(RoleChecker([UserRole.SUPERADMIN, UserRole.ADMIN])),
) -> None:
    await service.revoke(user_id, invitation_id)


@router.post("/invitations/accept", response_model=InvitationAcceptResponse)
async def accept_invitation(
    payload: InvitationAcceptRequest,
    service: TeamService = Depends(get_team_service),
) -> InvitationAcceptResponse:
    return await service.accept(payload)


@router.get("/seats", response_model=SeatUsageResponse)
async def get_seats(
    company_id: Optional[int] = None,
    service: TeamService = Depends(get_team_service),
    user_id: int = Depends(RoleChecker([UserRole.SUPERADMIN, UserRole.ADMIN])),
) -> SeatUsageResponse:
    return await service.seats(user_id, company_id)
