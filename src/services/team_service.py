"""Tenant invitation and seat-management service."""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional

from argon2 import PasswordHasher
from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.auth.jwt_handler import create_token_pair
from src.config.config import settings
from src.core.enums import AuditAction, InvitationStatus, TableName, UserRole
from src.models import (
    AuditLog,
    Company,
    CompanyLocationAccess,
    CompanyStaff,
    TenantInvitation,
    User,
    UserLocationAccess,
)
from src.schemas import (
    InvitationAcceptRequest,
    InvitationAcceptResponse,
    InvitationCreatedResponse,
    InvitationCreateRequest,
    InvitationResponse,
    SeatUsageResponse,
)
from src.services.email_service import EmailService
from src.services.lifecycle_service import LifecycleService
from src.services.subscription_service import SubscriptionService


class TeamService:
    """Create and consume tenant-scoped invitations."""

    def __init__(
        self,
        session: AsyncSession,
        email_service: Optional[EmailService] = None,
    ) -> None:
        self.session = session
        self.email_service = email_service or EmailService()
        self.subscription_service = SubscriptionService(session)
        self.lifecycle_service = LifecycleService(session, self.email_service)
        self.password_hasher = PasswordHasher()

    async def create(
        self,
        requester_id: int,
        payload: InvitationCreateRequest,
    ) -> InvitationCreatedResponse:
        requester = await self._requester(requester_id)
        company_id = await self._target_company(
            requester_id,
            payload.company_id,
        )
        self._validate_role(requester, payload.role)
        await self._validate_location(company_id, payload.location_id)
        await self._ensure_identity_available(payload.email, payload.username)
        await self._enforce_reserved_seat(company_id, payload.role)

        existing = await self.session.execute(
            select(TenantInvitation).where(
                TenantInvitation.company_id == company_id,
                TenantInvitation.email == str(payload.email),
                TenantInvitation.status == InvitationStatus.PENDING,
                TenantInvitation.expires_at > datetime.now(),
            )
        )
        if existing.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A pending invitation already exists for this email.",
            )

        raw_token = secrets.token_urlsafe(32)
        invitation = TenantInvitation(
            company_id=company_id,
            location_id=payload.location_id,
            invited_by=requester_id,
            email=str(payload.email),
            full_name=payload.full_name,
            username=payload.username,
            role=payload.role,
            token_hash=self._hash(raw_token),
            expires_at=datetime.now()
            + timedelta(hours=settings.INVITATION_EXPIRE_HOURS),
        )
        self.session.add(invitation)
        await self.session.flush()
        self._audit(
            requester_id,
            AuditAction.CREATE,
            invitation.id,
            "Tenant invitation created.",
        )
        await self.session.commit()
        await self._send_invitation(invitation, raw_token)
        return self._created_response(invitation, raw_token)

    async def list(
        self,
        requester_id: int,
        company_id: Optional[int],
    ) -> list[InvitationResponse]:
        root_id = await self.subscription_service.resolve_company_for_billing(
            requester_id,
            company_id,
        )
        company_ids = await self.subscription_service._tenant_company_ids(root_id)
        result = await self.session.execute(
            select(TenantInvitation)
            .where(TenantInvitation.company_id.in_(company_ids))
            .order_by(TenantInvitation.created_at.desc())
        )
        invitations = list(result.scalars().all())
        changed = False
        for invitation in invitations:
            if (
                invitation.status == InvitationStatus.PENDING
                and invitation.expires_at <= datetime.now()
            ):
                invitation.status = InvitationStatus.EXPIRED
                invitation.updated_at = datetime.now()
                changed = True
        if changed:
            await self.session.commit()
        return [self._response(item) for item in invitations]

    async def revoke(self, requester_id: int, invitation_id: int) -> None:
        invitation = await self._authorized_invitation(requester_id, invitation_id)
        if invitation.status != InvitationStatus.PENDING:
            raise HTTPException(status_code=409, detail="Invitation is not pending.")
        invitation.status = InvitationStatus.REVOKED
        invitation.revoked_at = datetime.now()
        invitation.updated_at = datetime.now()
        self._audit(
            requester_id,
            AuditAction.DELETE,
            invitation.id,
            "Tenant invitation revoked.",
        )
        await self.session.commit()

    async def resend(
        self,
        requester_id: int,
        invitation_id: int,
    ) -> InvitationCreatedResponse:
        invitation = await self._authorized_invitation(requester_id, invitation_id)
        if invitation.status == InvitationStatus.ACCEPTED:
            raise HTTPException(
                status_code=409, detail="Invitation was already accepted."
            )
        raw_token = secrets.token_urlsafe(32)
        invitation.token_hash = self._hash(raw_token)
        invitation.status = InvitationStatus.PENDING
        invitation.expires_at = datetime.now() + timedelta(
            hours=settings.INVITATION_EXPIRE_HOURS
        )
        invitation.revoked_at = None
        invitation.resend_count += 1
        invitation.updated_at = datetime.now()
        self._audit(
            requester_id,
            AuditAction.UPDATE,
            invitation.id,
            "Tenant invitation resent.",
        )
        await self.session.commit()
        await self._send_invitation(invitation, raw_token)
        return self._created_response(invitation, raw_token)

    async def accept(
        self,
        payload: InvitationAcceptRequest,
    ) -> InvitationAcceptResponse:
        result = await self.session.execute(
            select(TenantInvitation)
            .where(TenantInvitation.token_hash == self._hash(payload.token))
            .with_for_update()
        )
        invitation = result.scalars().first()
        if (
            not invitation
            or invitation.status != InvitationStatus.PENDING
            or invitation.expires_at <= datetime.now()
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invitation is invalid or expired.",
            )
        await self._ensure_identity_available(invitation.email, invitation.username)
        if invitation.role in {UserRole.ADMIN, UserRole.OPERATOR}:
            resource = "admins" if invitation.role == UserRole.ADMIN else "operators"
            await self.subscription_service.enforce_limit(
                invitation.company_id,
                resource,
            )

        user = User(
            username=invitation.username,
            full_name=invitation.full_name,
            email=invitation.email,
            password_hash=self.password_hasher.hash(payload.password),
            role=invitation.role,
            status=True,
            is_active=True,
            email_verified_at=datetime.now(),
            created_by=invitation.invited_by,
        )
        self.session.add(user)
        await self.session.flush()
        self.session.add(
            CompanyStaff(
                company_id=invitation.company_id,
                user_id=user.id,
                created_by=invitation.invited_by,
            )
        )
        if invitation.location_id:
            self.session.add(
                UserLocationAccess(
                    user_id=user.id,
                    location_id=invitation.location_id,
                    created_by=invitation.invited_by,
                )
            )
        invitation.status = InvitationStatus.ACCEPTED
        invitation.accepted_at = datetime.now()
        invitation.updated_at = datetime.now()
        tokens = create_token_pair(user.id, user.role)
        user.refresh_token = self._hash(tokens["refresh_token"])
        self._audit(
            invitation.invited_by,
            AuditAction.ACCESS_GRANTED,
            invitation.id,
            "Tenant invitation accepted.",
        )
        await self.lifecycle_service.queue_email(
            event_key=f"welcome-invited:{user.id}",
            company_id=invitation.company_id,
            user_id=user.id,
            recipient=user.email,
            subject="Bienvenido a Locentr",
            title="Tu acceso está listo",
            message="Ya puedes colaborar en la operación asignada.",
            action_url=f"{settings.FRONT_URL_BASE}/dashboard",
            action_label="Entrar a Locentr",
        )
        await self.session.commit()
        return InvitationAcceptResponse(
            **tokens,
            company_id=invitation.company_id,
        )

    async def seats(
        self,
        requester_id: int,
        company_id: Optional[int],
    ) -> SeatUsageResponse:
        root_id = await self.subscription_service.resolve_company_for_billing(
            requester_id,
            company_id,
        )
        subscription = await self.subscription_service._subscription(root_id)
        usage = await self.subscription_service.usage(root_id)
        company_ids = await self.subscription_service._tenant_company_ids(root_id)
        pending_admins = await self._pending_count(company_ids, UserRole.ADMIN)
        pending_operators = await self._pending_count(company_ids, UserRole.OPERATOR)
        return SeatUsageResponse(
            admins_used=usage.admins,
            admins_limit=subscription.plan.qty_admins,
            operators_used=usage.operators,
            operators_limit=subscription.plan.qty_operators,
            pending_admins=pending_admins,
            pending_operators=pending_operators,
        )

    async def _requester(self, requester_id: int) -> User:
        requester = await self.session.get(User, requester_id)
        if not requester or not requester.is_active:
            raise HTTPException(status_code=404, detail="User not found.")
        return requester

    async def _target_company(
        self,
        requester_id: int,
        requested_company_id: Optional[int],
    ) -> int:
        root_id = await self.subscription_service.resolve_company_for_billing(
            requester_id,
            requested_company_id,
        )
        target_id = requested_company_id or root_id
        target = await self.session.get(Company, target_id)
        if not target or (target.parent_company_id or target.id) != root_id:
            raise HTTPException(status_code=403, detail="Not allowed for this company.")
        return target_id

    async def _authorized_invitation(
        self,
        requester_id: int,
        invitation_id: int,
    ) -> TenantInvitation:
        invitation = await self.session.get(TenantInvitation, invitation_id)
        if not invitation:
            raise HTTPException(status_code=404, detail="Invitation not found.")
        await self._target_company(requester_id, invitation.company_id)
        return invitation

    def _validate_role(self, requester: User, role: UserRole) -> None:
        if role == UserRole.SUPERADMIN:
            raise HTTPException(status_code=403, detail="SUPERADMIN cannot be invited.")
        if requester.role == UserRole.ADMIN and role == UserRole.ADMIN:
            raise HTTPException(
                status_code=403, detail="ADMIN cannot invite administrators."
            )

    async def _validate_location(
        self,
        company_id: int,
        location_id: Optional[int],
    ) -> None:
        if not location_id:
            return
        result = await self.session.execute(
            select(CompanyLocationAccess.id).where(
                CompanyLocationAccess.company_id == company_id,
                CompanyLocationAccess.location_id == location_id,
            )
        )
        if not result.scalars().first():
            raise HTTPException(
                status_code=403, detail="Location is outside the company."
            )

    async def _ensure_identity_available(self, email: str, username: str) -> None:
        result = await self.session.execute(
            select(User.id).where(
                (User.email == str(email)) | (User.username == username)
            )
        )
        if result.scalars().first():
            raise HTTPException(
                status_code=409, detail="Email or username is already registered."
            )

    async def _enforce_reserved_seat(self, company_id: int, role: UserRole) -> None:
        if role not in {UserRole.ADMIN, UserRole.OPERATOR}:
            return
        root_id = await self.subscription_service._root_company_id(company_id)
        subscription = await self.subscription_service._subscription(root_id)
        usage = await self.subscription_service.usage(root_id)
        company_ids = await self.subscription_service._tenant_company_ids(root_id)
        pending = await self._pending_count(company_ids, role)
        current = usage.admins if role == UserRole.ADMIN else usage.operators
        limit = (
            subscription.plan.qty_admins
            if role == UserRole.ADMIN
            else subscription.plan.qty_operators
        )
        if current + pending + 1 > limit:
            raise HTTPException(status_code=409, detail="Plan seat limit reached.")

    async def _pending_count(self, company_ids: list[int], role: UserRole) -> int:
        value = await self.session.scalar(
            select(func.count(TenantInvitation.id)).where(
                TenantInvitation.company_id.in_(company_ids),
                TenantInvitation.role == role,
                TenantInvitation.status == InvitationStatus.PENDING,
                TenantInvitation.expires_at > datetime.now(),
            )
        )
        return int(value or 0)

    async def _send_invitation(
        self,
        invitation: TenantInvitation,
        raw_token: str,
    ) -> None:
        self.email_service.send_templated_email(
            invitation.email,
            "Te invitaron a Locentr",
            "transactional.html",
            {
                "title": "Únete a la operación",
                "message": "Crea tu contraseña para aceptar la invitación.",
                "action_url": (
                    f"{settings.FRONT_URL_BASE}/accept-invitation?token={raw_token}"
                ),
                "action_label": "Aceptar invitación",
            },
        )

    def _audit(
        self,
        user_id: int,
        action: AuditAction,
        record_id: int,
        description: str,
    ) -> None:
        self.session.add(
            AuditLog(
                user_id=user_id,
                action=action,
                table_name=TableName.USERS,
                record_id=record_id,
                description=description,
            )
        )

    @staticmethod
    def _hash(value: str) -> str:
        return hashlib.sha256(value.encode()).hexdigest()

    def _response(self, invitation: TenantInvitation) -> InvitationResponse:
        return InvitationResponse.model_validate(invitation, from_attributes=True)

    def _created_response(
        self,
        invitation: TenantInvitation,
        raw_token: str,
    ) -> InvitationCreatedResponse:
        return InvitationCreatedResponse(
            **self._response(invitation).model_dump(),
            invitation_url=(
                f"{settings.FRONT_URL_BASE}/accept-invitation?token={raw_token}"
            ),
        )
