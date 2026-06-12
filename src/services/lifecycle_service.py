"""Transactional communication, verification and billing history."""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.config.config import settings
from src.core.enums import SubscriptionStatus, UserRole
from src.models import (
    BillingInvoice,
    CommunicationPreference,
    CompanyStaff,
    CompanySubscription,
    EmailDelivery,
    EmailVerificationToken,
    User,
)
from src.services.email_service import EmailService


class LifecycleService:
    """Manage the durable billing and communication lifecycle."""

    def __init__(
        self,
        session: AsyncSession,
        email_service: Optional[EmailService] = None,
    ) -> None:
        self.session = session
        self.email_service = email_service or EmailService()

    async def queue_email(
        self,
        *,
        event_key: str,
        recipient: str,
        subject: str,
        title: str,
        message: str,
        company_id: Optional[int] = None,
        user_id: Optional[int] = None,
        action_url: Optional[str] = None,
        action_label: str = "Abrir Locentr",
    ) -> bool:
        """Insert one idempotent outbox record."""
        existing = await self.session.execute(
            select(EmailDelivery.id).where(EmailDelivery.event_key == event_key)
        )
        if existing.scalars().first():
            return False
        self.session.add(
            EmailDelivery(
                event_key=event_key,
                company_id=company_id,
                user_id=user_id,
                recipient=recipient,
                subject=subject,
                template_name="transactional.html",
                context={
                    "title": title,
                    "message": message,
                    "action_url": action_url,
                    "action_label": action_label,
                },
            )
        )
        return True

    async def create_email_verification(self, user: User, company_id: int) -> str:
        """Create a hashed verification token and queue its email."""
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        self.session.add(
            EmailVerificationToken(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=datetime.now()
                + timedelta(hours=settings.EMAIL_VERIFICATION_EXPIRE_HOURS),
            )
        )
        await self.queue_email(
            event_key=f"verify-email:{user.id}:{token_hash[:12]}",
            company_id=company_id,
            user_id=user.id,
            recipient=user.email,
            subject="Verifica tu correo en Locentr",
            title="Confirma tu correo",
            message="Activa tu cuenta para mantener segura la administración.",
            action_url=f"{settings.FRONT_URL_BASE}/verify-email?token={raw_token}",
            action_label="Verificar correo",
        )
        return raw_token

    async def verify_email(self, raw_token: str) -> None:
        """Consume a valid verification token once."""
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        result = await self.session.execute(
            select(EmailVerificationToken)
            .where(EmailVerificationToken.token_hash == token_hash)
            .with_for_update()
        )
        token = result.scalars().first()
        if not token or token.consumed_at or token.expires_at <= datetime.now():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification token is invalid or expired.",
            )
        user = await self.session.get(User, token.user_id)
        if not user or not user.is_active:
            raise HTTPException(status_code=404, detail="User not found.")
        now = datetime.now()
        user.email_verified_at = now
        token.consumed_at = now
        await self.session.commit()

    async def queue_trial_reminders(self, secret: str) -> int:
        """Queue 7, 3 and 1 day trial reminders without duplicates."""
        self._validate_queue_secret(secret)
        result = await self.session.execute(
            select(CompanySubscription).where(
                CompanySubscription.status == SubscriptionStatus.TRIALING,
                CompanySubscription.trial_ends_at > datetime.now(),
            )
        )
        queued = 0
        for subscription in result.scalars().all():
            days = (subscription.trial_ends_at.date() - datetime.now().date()).days
            if days not in {7, 3, 1}:
                continue
            for admin in await self.company_admins(subscription.company_id):
                queued += int(
                    await self.queue_email(
                        event_key=f"trial:{subscription.id}:{days}:{admin.id}",
                        company_id=subscription.company_id,
                        user_id=admin.id,
                        recipient=admin.email,
                        subject=f"Tu prueba de Locentr termina en {days} día(s)",
                        title="Tu prueba está por terminar",
                        message=(
                            f"Quedan {days} día(s). Elige un plan para mantener "
                            "activa tu operación."
                        ),
                        action_url=f"{settings.FRONT_URL_BASE}/settings/billing",
                        action_label="Revisar planes",
                    )
                )
        await self.session.commit()
        return queued

    async def process_queue(self, secret: str) -> tuple[int, int]:
        """Deliver due outbox records with bounded exponential retry."""
        self._validate_queue_secret(secret)
        result = await self.session.execute(
            select(EmailDelivery)
            .where(
                EmailDelivery.status.in_(["PENDING", "FAILED"]),
                EmailDelivery.attempts < 5,
                EmailDelivery.scheduled_for <= datetime.now(),
            )
            .order_by(EmailDelivery.created_at)
            .limit(50)
            .with_for_update(skip_locked=True)
        )
        sent = failed = 0
        for delivery in result.scalars().all():
            delivery.attempts += 1
            delivery.updated_at = datetime.now()
            try:
                self.email_service.send_templated_email(
                    delivery.recipient,
                    delivery.subject,
                    delivery.template_name,
                    delivery.context,
                )
                delivery.status = "SENT"
                delivery.sent_at = datetime.now()
                delivery.last_error = None
                sent += 1
            except Exception:  # provider details stay out of persistence and API
                delivery.status = "FAILED"
                delivery.last_error = "Provider delivery failed."
                delivery.scheduled_for = datetime.now() + timedelta(
                    minutes=min(60, 2**delivery.attempts)
                )
                failed += 1
        await self.session.commit()
        return sent, failed

    async def preferences(
        self,
        company_id: int,
        user_id: int,
        billing: Optional[bool] = None,
        product: Optional[bool] = None,
    ) -> CommunicationPreference:
        """Read or update company communication preferences."""
        result = await self.session.execute(
            select(CommunicationPreference).where(
                CommunicationPreference.company_id == company_id
            )
        )
        preference = result.scalars().first()
        if not preference:
            preference = CommunicationPreference(
                company_id=company_id,
                updated_by=user_id,
            )
            self.session.add(preference)
        if billing is not None:
            preference.billing_emails = billing
        if product is not None:
            preference.product_emails = product
        preference.updated_by = user_id
        preference.updated_at = datetime.now()
        await self.session.commit()
        await self.session.refresh(preference)
        return preference

    async def invoices(self, company_id: int) -> list[BillingInvoice]:
        """Return newest invoices first."""
        result = await self.session.execute(
            select(BillingInvoice)
            .where(BillingInvoice.company_id == company_id)
            .order_by(BillingInvoice.created_at.desc())
        )
        return list(result.scalars().all())

    async def upsert_invoice(self, company_id: int, data: Any) -> BillingInvoice:
        """Store sanitized provider invoice metadata."""
        provider_id = str(data.get("id"))
        result = await self.session.execute(
            select(BillingInvoice).where(
                BillingInvoice.provider_invoice_id == provider_id
            )
        )
        invoice = result.scalars().first()
        if not invoice:
            invoice = BillingInvoice(
                company_id=company_id,
                provider_invoice_id=provider_id,
                status=str(data.get("status") or "open"),
            )
            self.session.add(invoice)
        invoice.status = str(data.get("status") or invoice.status)
        invoice.currency = str(data.get("currency") or "usd")
        invoice.amount_due = int(data.get("amount_due") or 0)
        invoice.amount_paid = int(data.get("amount_paid") or 0)
        invoice.hosted_invoice_url = data.get("hosted_invoice_url")
        invoice.invoice_pdf = data.get("invoice_pdf")
        lines = data.get("lines", {}).get("data", [])
        period = lines[0].get("period", {}) if lines else {}
        invoice.period_start = self._timestamp(period.get("start"))
        invoice.period_end = self._timestamp(period.get("end"))
        invoice.updated_at = datetime.now()
        return invoice

    async def billing_emails_enabled(self, company_id: int) -> bool:
        result = await self.session.execute(
            select(CommunicationPreference.billing_emails).where(
                CommunicationPreference.company_id == company_id
            )
        )
        value = result.scalars().first()
        return True if value is None else bool(value)

    async def company_admins(self, company_id: int) -> list[User]:
        result = await self.session.execute(
            select(User)
            .join(CompanyStaff, CompanyStaff.user_id == User.id)
            .where(
                CompanyStaff.company_id == company_id,
                User.is_active.is_(True),
                User.role == UserRole.ADMIN,
            )
        )
        return list(result.scalars().all())

    def _validate_queue_secret(self, secret: str) -> None:
        if not settings.EMAIL_QUEUE_SECRET or secret != settings.EMAIL_QUEUE_SECRET:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email queue secret.",
            )

    @staticmethod
    def _timestamp(value: Any) -> Optional[datetime]:
        return datetime.fromtimestamp(int(value)) if value else None
