"""Plans, company subscriptions, checkout, portal and Stripe webhooks."""

from typing import Optional

from fastapi import APIRouter, Depends, Header, Request, status

from src.auth.permissions import RoleChecker
from src.core.enums import UserRole
from src.dependencies import get_subscription_service
from src.schemas import (
    BillingCompanyRequest,
    BillingRedirectResponse,
    CheckoutSessionRequest,
    CompanySubscriptionResponse,
    PlanResponse,
    StartTrialRequest,
    StartTrialResponse,
    ReconciliationResponse,
)
from src.services.subscription_service import SubscriptionService

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.post(
    "/trial",
    response_model=StartTrialResponse,
    status_code=status.HTTP_201_CREATED,
)
async def start_trial(
    payload: StartTrialRequest,
    service: SubscriptionService = Depends(get_subscription_service),
) -> StartTrialResponse:
    """Create and authenticate a new 14-day trial tenant."""
    return await service.start_trial(payload)


@router.get("/plans", response_model=list[PlanResponse])
async def list_plans(
    service: SubscriptionService = Depends(get_subscription_service),
) -> list[PlanResponse]:
    """Return the public plan catalog."""
    return await service.list_plans()


@router.get("/me", response_model=CompanySubscriptionResponse)
async def get_my_subscription(
    company_id: Optional[int] = None,
    service: SubscriptionService = Depends(get_subscription_service),
    user_id: int = Depends(
        RoleChecker([UserRole.SUPERADMIN, UserRole.ADMIN]),
    ),
) -> CompanySubscriptionResponse:
    """Return plan, trial and usage for an authorized tenant."""
    return await service.get_summary(user_id, company_id)


@router.post("/checkout", response_model=BillingRedirectResponse)
async def create_checkout(
    payload: CheckoutSessionRequest,
    service: SubscriptionService = Depends(get_subscription_service),
    user_id: int = Depends(
        RoleChecker([UserRole.SUPERADMIN, UserRole.ADMIN]),
    ),
) -> BillingRedirectResponse:
    """Create a Stripe subscription Checkout Session."""
    url = await service.create_checkout(
        user_id=user_id,
        plan_code=payload.plan_code,
        company_id=payload.company_id,
    )
    return BillingRedirectResponse(url=url)


@router.post("/portal", response_model=BillingRedirectResponse)
async def create_billing_portal(
    payload: BillingCompanyRequest,
    service: SubscriptionService = Depends(get_subscription_service),
    user_id: int = Depends(
        RoleChecker([UserRole.SUPERADMIN, UserRole.ADMIN]),
    ),
) -> BillingRedirectResponse:
    """Create a Stripe customer portal session."""
    url = await service.create_portal(user_id, payload.company_id)
    return BillingRedirectResponse(url=url)


@router.post("/stripe/webhook", status_code=status.HTTP_204_NO_CONTENT)
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(alias="Stripe-Signature"),
    service: SubscriptionService = Depends(get_subscription_service),
) -> None:
    """Verify and apply a raw Stripe webhook payload."""
    await service.process_stripe_webhook(
        payload=await request.body(),
        signature=stripe_signature,
    )


@router.post("/reconcile", response_model=ReconciliationResponse)
async def reconcile_subscriptions(
    reconciliation_secret: str = Header(alias="X-Reconciliation-Secret"),
    service: SubscriptionService = Depends(get_subscription_service),
) -> ReconciliationResponse:
    """Expire trials from a trusted scheduled job."""
    expired = await service.reconcile_expired_trials(reconciliation_secret)
    return ReconciliationResponse(expired_trials=expired)
