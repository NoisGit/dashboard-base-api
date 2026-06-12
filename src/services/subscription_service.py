"""Company-owned plans, trials, entitlements and Stripe synchronization."""

import asyncio
import hashlib
from datetime import datetime, timedelta
from typing import Any, Optional

import stripe
from argon2 import PasswordHasher
from fastapi import HTTPException, status
from sqlalchemy import distinct, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from src.config.config import settings
from src.core.enums import SubscriptionStatus, UserRole
from src.models import (
    AccessLog,
    BillingEvent,
    Company,
    CompanyLocationAccess,
    CompanyStaff,
    CompanySubscription,
    Document,
    Location,
    Plan,
    User,
)
from src.auth.jwt_handler import create_token_pair
from src.schemas import (
    CompanySubscriptionResponse,
    PlanResponse,
    SubscriptionUsageResponse,
    StartTrialRequest,
    StartTrialResponse,
)


class SubscriptionService:
    """Manage one commercial subscription per root company tenant."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.password_hasher = PasswordHasher()

    async def start_trial(
        self,
        payload: StartTrialRequest,
    ) -> StartTrialResponse:
        """Atomically create a root tenant, first admin and first location."""
        duplicate_user = await self.session.execute(
            select(User).where(
                (User.email == str(payload.admin.email))
                | (User.username == payload.admin.username)
            )
        )
        if duplicate_user.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The administrator email or username is already registered.",
            )
        duplicate_company = await self.session.execute(
            select(Company).where(
                Company.parent_company_id.is_(None),
                Company.id_number == payload.company.id_number,
            )
        )
        if duplicate_company.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A trial already exists for this company identifier.",
            )

        admin = User(
            username=payload.admin.username,
            full_name=payload.admin.full_name,
            email=str(payload.admin.email),
            password_hash=self.password_hasher.hash(payload.admin.password),
            role=UserRole.ADMIN,
            status=True,
            is_active=True,
            created_at=datetime.now(),
        )
        self.session.add(admin)
        await self.session.flush()

        company = Company(
            name=payload.company.name,
            activity=payload.company.activity,
            id_number=payload.company.id_number,
            type_document=payload.company.type_document,
            created_by=admin.id,
        )
        self.session.add(company)
        await self.session.flush()
        subscription = await self.create_trial(company.id)

        self.session.add(
            CompanyStaff(
                company_id=company.id,
                user_id=admin.id,
                created_by=admin.id,
            )
        )
        location = Location(
            name=payload.location.name,
            address=payload.location.address,
            country=payload.location.country,
            is_active=True,
            created_by=admin.id,
        )
        self.session.add(location)
        await self.session.flush()
        self.session.add(
            CompanyLocationAccess(
                company_id=company.id,
                location_id=location.id,
                created_by=admin.id,
            )
        )

        tokens = create_token_pair(admin.id, admin.role)
        admin.refresh_token = hashlib.sha256(
            tokens["refresh_token"].encode("utf-8")
        ).hexdigest()
        await self.session.commit()
        return StartTrialResponse(
            **tokens,
            company_id=company.id,
            trial_ends_at=subscription.trial_ends_at,
        )

    async def list_plans(self) -> list[PlanResponse]:
        """Return active plans without exposing provider identifiers."""
        result = await self.session.execute(
            select(Plan)
            .where(Plan.is_active.is_(True))
            .order_by(Plan.monthly_price_cents)
        )
        return [self._plan_response(plan) for plan in result.scalars().all()]

    def _plan_response(self, plan: Plan) -> PlanResponse:
        return PlanResponse(
            code=plan.code,
            name=plan.name,
            description=plan.description,
            monthly_price_cents=plan.monthly_price_cents,
            qty_locations=plan.qty_locations,
            qty_admins=plan.qty_admins,
            qty_operators=plan.qty_operators,
            qty_daily_reads=plan.qty_daily_reads,
            qty_storage_bytes=plan.qty_storage_bytes,
            checkout_available=bool(
                settings.STRIPE_SECRET_KEY and self._stripe_price_id(plan)
            ),
        )

    def _stripe_price_id(self, plan: Plan) -> Optional[str]:
        configured = {
            "starter": settings.STRIPE_PRICE_STARTER,
            "growth": settings.STRIPE_PRICE_GROWTH,
            "scale": settings.STRIPE_PRICE_SCALE,
        }
        return configured.get(plan.code) or plan.stripe_price_id

    async def _root_company_id(self, company_id: int) -> int:
        company = await self.session.get(Company, company_id)
        if not company or not company.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found.",
            )
        return company.parent_company_id or company.id

    async def _company_id_for_user(self, user_id: int) -> Optional[int]:
        result = await self.session.execute(
            select(CompanyStaff.company_id).where(CompanyStaff.user_id == user_id)
        )
        return result.scalars().first()

    async def resolve_company_for_billing(
        self,
        user_id: int,
        requested_company_id: Optional[int] = None,
    ) -> int:
        """Resolve and authorize the root company used for billing."""
        user = await self.session.get(User, user_id)
        if not user or not user.is_active:
            raise HTTPException(status_code=404, detail="User not found.")

        if user.role == UserRole.SUPERADMIN:
            if requested_company_id is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="company_id is required for SUPERADMIN billing actions.",
                )
            return await self._root_company_id(requested_company_id)

        assigned_company_id = await self._company_id_for_user(user_id)
        if assigned_company_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is not assigned to a company.",
            )
        root_company_id = await self._root_company_id(assigned_company_id)
        if (
            requested_company_id is not None
            and await self._root_company_id(requested_company_id) != root_company_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not allowed for this subscription.",
            )
        return root_company_id

    async def create_trial(self, company_id: int) -> CompanySubscription:
        """Create the tenant's only trial without allowing resets."""
        root_company_id = await self._root_company_id(company_id)
        existing_result = await self.session.execute(
            select(CompanySubscription).where(
                CompanySubscription.company_id == root_company_id
            )
        )
        existing = existing_result.scalars().first()
        if existing:
            return existing

        plan_result = await self.session.execute(
            select(Plan).where(Plan.code == settings.trial_plan_code)
        )
        plan = plan_result.scalars().first()
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Trial plan is not configured.",
            )

        now = datetime.now()
        subscription = CompanySubscription(
            company_id=root_company_id,
            plan_id=plan.id,
            status=SubscriptionStatus.TRIALING,
            trial_started_at=now,
            trial_ends_at=now + timedelta(days=settings.trial_days),
            provider="stripe",
            created_at=now,
            updated_at=now,
        )
        self.session.add(subscription)
        await self.session.flush()
        return subscription

    async def _subscription(
        self,
        company_id: int,
        for_update: bool = False,
    ) -> CompanySubscription:
        root_company_id = await self._root_company_id(company_id)
        stmt = (
            select(CompanySubscription)
            .where(CompanySubscription.company_id == root_company_id)
            .options(selectinload(CompanySubscription.plan))
        )
        if for_update:
            stmt = stmt.with_for_update()
        result = await self.session.execute(stmt)
        subscription = result.scalars().first()
        if not subscription:
            subscription = await self.create_trial(root_company_id)
            await self.session.refresh(subscription, attribute_names=["plan"])

        if (
            subscription.status == SubscriptionStatus.TRIALING
            and datetime.now() >= subscription.trial_ends_at
        ):
            subscription.status = SubscriptionStatus.CANCELED
            subscription.canceled_at = datetime.now()
            subscription.updated_at = datetime.now()
            await self.session.flush()
        return subscription

    async def _tenant_company_ids(self, root_company_id: int) -> list[int]:
        result = await self.session.execute(
            select(Company.id).where(
                (Company.id == root_company_id)
                | (Company.parent_company_id == root_company_id)
            )
        )
        return list(result.scalars().all())

    async def usage(self, root_company_id: int) -> SubscriptionUsageResponse:
        """Measure current tenant usage from authoritative records."""
        company_ids = await self._tenant_company_ids(root_company_id)
        locations = await self.session.scalar(
            select(func.count(distinct(Location.id)))
            .join(
                CompanyLocationAccess,
                CompanyLocationAccess.location_id == Location.id,
            )
            .where(
                CompanyLocationAccess.company_id.in_(company_ids),
                Location.is_active.is_(True),
            )
        )
        admins = await self.session.scalar(
            select(func.count(distinct(User.id)))
            .join(CompanyStaff, CompanyStaff.user_id == User.id)
            .where(
                CompanyStaff.company_id.in_(company_ids),
                User.role == UserRole.ADMIN,
                User.is_active.is_(True),
            )
        )
        operators = await self.session.scalar(
            select(func.count(distinct(User.id)))
            .join(CompanyStaff, CompanyStaff.user_id == User.id)
            .where(
                CompanyStaff.company_id.in_(company_ids),
                User.role == UserRole.OPERATOR,
                User.is_active.is_(True),
            )
        )
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        daily_reads = await self.session.scalar(
            select(func.count(distinct(AccessLog.id)))
            .join(
                CompanyLocationAccess,
                CompanyLocationAccess.location_id == AccessLog.location_id,
            )
            .where(
                CompanyLocationAccess.company_id.in_(company_ids),
                AccessLog.created_at >= today,
            )
        )
        storage_bytes = await self.session.scalar(
            select(func.coalesce(func.sum(Document.size_bytes), 0)).where(
                Document.company_id.in_(company_ids)
            )
        )
        return SubscriptionUsageResponse(
            locations=int(locations or 0),
            admins=int(admins or 0),
            operators=int(operators or 0),
            daily_reads=int(daily_reads or 0),
            storage_bytes=int(storage_bytes or 0),
        )

    async def get_summary(
        self,
        user_id: int,
        company_id: Optional[int] = None,
    ) -> CompanySubscriptionResponse:
        """Return subscription and usage for an authorized administrator."""
        root_company_id = await self.resolve_company_for_billing(user_id, company_id)
        subscription = await self._subscription(root_company_id)
        usage = await self.usage(root_company_id)
        return CompanySubscriptionResponse(
            company_id=root_company_id,
            status=subscription.status,
            trial_started_at=subscription.trial_started_at,
            trial_ends_at=subscription.trial_ends_at,
            current_period_end=subscription.current_period_end,
            plan=self._plan_response(subscription.plan),
            usage=usage,
        )

    async def enforce_limit(
        self,
        company_id: int,
        resource: str,
        increment: int = 1,
    ) -> None:
        """Atomically reject provisioning beyond the active plan."""
        subscription = await self._subscription(company_id, for_update=True)
        if subscription.status not in {
            SubscriptionStatus.TRIALING,
            SubscriptionStatus.ACTIVE,
        }:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="The company subscription is not active.",
            )

        usage = await self.usage(subscription.company_id)
        limits = {
            "locations": subscription.plan.qty_locations,
            "admins": subscription.plan.qty_admins,
            "operators": subscription.plan.qty_operators,
            "daily_reads": subscription.plan.qty_daily_reads,
            "storage_bytes": subscription.plan.qty_storage_bytes,
        }
        current = getattr(usage, resource, None)
        limit = limits.get(resource)
        if current is None or limit is None:
            raise ValueError(f"Unknown entitlement resource: {resource}")
        if current + increment > limit:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Plan limit reached for {resource}.",
            )

    async def create_checkout(
        self,
        user_id: int,
        plan_code: str,
        company_id: Optional[int] = None,
    ) -> str:
        """Create a Stripe subscription checkout for an authorized tenant."""
        if not settings.STRIPE_SECRET_KEY:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Stripe is not configured.",
            )
        root_company_id = await self.resolve_company_for_billing(user_id, company_id)
        subscription = await self._subscription(root_company_id)
        plan_result = await self.session.execute(
            select(Plan).where(
                Plan.code == plan_code,
                Plan.is_active.is_(True),
            )
        )
        plan = plan_result.scalars().first()
        price_id = self._stripe_price_id(plan) if plan else None
        if not plan or not price_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This plan is not available for checkout.",
            )

        stripe.api_key = settings.STRIPE_SECRET_KEY
        metadata = {
            "company_id": str(root_company_id),
            "plan_code": plan.code,
        }
        checkout_args: dict[str, Any] = {
            "mode": "subscription",
            "line_items": [{"price": price_id, "quantity": 1}],
            "success_url": f"{settings.FRONT_URL_BASE}/settings/billing?checkout=success",
            "cancel_url": f"{settings.FRONT_URL_BASE}/settings/billing?checkout=cancel",
            "client_reference_id": str(root_company_id),
            "metadata": metadata,
            "subscription_data": {"metadata": metadata},
        }
        if subscription.provider_customer_id:
            checkout_args["customer"] = subscription.provider_customer_id
        if (
            subscription.status == SubscriptionStatus.TRIALING
            and subscription.trial_ends_at > datetime.now() + timedelta(minutes=5)
        ):
            checkout_args["subscription_data"]["trial_end"] = int(
                subscription.trial_ends_at.timestamp()
            )

        checkout = await asyncio.to_thread(
            stripe.checkout.Session.create,
            **checkout_args,
        )
        if not checkout.url:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Stripe did not return a checkout URL.",
            )
        return checkout.url

    async def create_portal(
        self,
        user_id: int,
        company_id: Optional[int] = None,
    ) -> str:
        """Create a Stripe customer portal session."""
        if not settings.STRIPE_SECRET_KEY:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Stripe is not configured.",
            )
        root_company_id = await self.resolve_company_for_billing(user_id, company_id)
        subscription = await self._subscription(root_company_id)
        if not subscription.provider_customer_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The company has no Stripe customer yet.",
            )
        stripe.api_key = settings.STRIPE_SECRET_KEY
        portal = await asyncio.to_thread(
            stripe.billing_portal.Session.create,
            customer=subscription.provider_customer_id,
            return_url=f"{settings.FRONT_URL_BASE}/settings/billing",
        )
        return portal.url

    async def reconcile_expired_trials(self, secret: str) -> int:
        """Expire trials from a scheduler even when no user opens the app."""
        if (
            not settings.BILLING_RECONCILIATION_SECRET
            or secret != settings.BILLING_RECONCILIATION_SECRET
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid billing reconciliation secret.",
            )
        result = await self.session.execute(
            select(CompanySubscription)
            .where(
                CompanySubscription.status == SubscriptionStatus.TRIALING,
                CompanySubscription.trial_ends_at <= datetime.now(),
            )
            .with_for_update()
        )
        subscriptions = list(result.scalars().all())
        now = datetime.now()
        for subscription in subscriptions:
            subscription.status = SubscriptionStatus.CANCELED
            subscription.canceled_at = now
            subscription.updated_at = now
        await self.session.commit()
        return len(subscriptions)

    async def process_stripe_webhook(
        self,
        payload: bytes,
        signature: str,
    ) -> None:
        """Verify and idempotently apply a Stripe subscription event."""
        if not settings.STRIPE_WEBHOOK_SECRET:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Stripe webhook is not configured.",
            )
        try:
            event = stripe.Webhook.construct_event(
                payload,
                signature,
                settings.STRIPE_WEBHOOK_SECRET,
            )
        except (ValueError, stripe.SignatureVerificationError) as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Stripe webhook signature.",
            ) from exc

        event_id = str(event["id"])
        existing = await self.session.execute(
            select(BillingEvent).where(
                BillingEvent.provider_event_id == event_id
            )
        )
        if existing.scalars().first():
            return

        event_type = str(event["type"])
        data_object = event["data"]["object"]
        await self._apply_stripe_event(event_type, data_object)
        self.session.add(
            BillingEvent(
                provider="stripe",
                provider_event_id=event_id,
                event_type=event_type,
            )
        )
        await self.session.commit()

    async def _apply_stripe_event(
        self,
        event_type: str,
        data_object: Any,
    ) -> None:
        metadata = dict(data_object.get("metadata") or {})
        company_id = metadata.get("company_id")
        plan_code = metadata.get("plan_code")
        customer_id = data_object.get("customer")

        subscription: Optional[CompanySubscription] = None
        if company_id:
            subscription = await self._subscription(int(company_id), for_update=True)
        elif customer_id:
            result = await self.session.execute(
                select(CompanySubscription)
                .where(CompanySubscription.provider_customer_id == customer_id)
                .options(selectinload(CompanySubscription.plan))
                .with_for_update()
            )
            subscription = result.scalars().first()
        if not subscription:
            return

        if plan_code:
            plan_result = await self.session.execute(
                select(Plan).where(Plan.code == plan_code)
            )
            plan = plan_result.scalars().first()
            if plan:
                subscription.plan_id = plan.id

        if event_type == "checkout.session.completed":
            subscription.provider_customer_id = customer_id
            subscription.provider_subscription_id = data_object.get("subscription")
        elif event_type in {
            "customer.subscription.created",
            "customer.subscription.updated",
        }:
            subscription.provider_customer_id = customer_id
            subscription.provider_subscription_id = data_object.get("id")
            subscription.status = self._map_stripe_status(data_object.get("status"))
            subscription.current_period_start = self._timestamp_to_datetime(
                data_object.get("current_period_start")
            )
            subscription.current_period_end = self._timestamp_to_datetime(
                data_object.get("current_period_end")
            )
        elif event_type == "customer.subscription.deleted":
            subscription.status = SubscriptionStatus.CANCELED
            subscription.canceled_at = datetime.now()
        elif event_type == "invoice.payment_failed":
            subscription.status = SubscriptionStatus.PAST_DUE
        elif event_type == "invoice.paid":
            subscription.status = SubscriptionStatus.ACTIVE

        subscription.updated_at = datetime.now()

    def _map_stripe_status(self, provider_status: Any) -> SubscriptionStatus:
        mapping = {
            "trialing": SubscriptionStatus.TRIALING,
            "active": SubscriptionStatus.ACTIVE,
            "past_due": SubscriptionStatus.PAST_DUE,
            "incomplete": SubscriptionStatus.PAST_DUE,
            "unpaid": SubscriptionStatus.CANCELED,
            "canceled": SubscriptionStatus.CANCELED,
            "incomplete_expired": SubscriptionStatus.CANCELED,
            "paused": SubscriptionStatus.CANCELED,
        }
        return mapping.get(str(provider_status), SubscriptionStatus.PAST_DUE)

    def _timestamp_to_datetime(self, value: Any) -> Optional[datetime]:
        if not value:
            return None
        return datetime.fromtimestamp(int(value))
