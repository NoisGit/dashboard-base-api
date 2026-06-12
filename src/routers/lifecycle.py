"""Email verification, communication preferences and billing history."""

from typing import Optional

from fastapi import APIRouter, Depends, Header

from src.auth.permissions import RoleChecker
from src.core.enums import UserRole
from src.dependencies import get_lifecycle_service, get_subscription_service
from src.schemas import (
    BillingInvoiceResponse,
    CommunicationPreferenceRequest,
    CommunicationPreferenceResponse,
    EmailVerificationRequest,
    QueueResultResponse,
)
from src.services.lifecycle_service import LifecycleService
from src.services.subscription_service import SubscriptionService

router = APIRouter(prefix="/lifecycle", tags=["lifecycle"])


@router.post("/verify-email", status_code=204)
async def verify_email(
    payload: EmailVerificationRequest,
    service: LifecycleService = Depends(get_lifecycle_service),
) -> None:
    await service.verify_email(payload.token)


@router.get(
    "/preferences",
    response_model=CommunicationPreferenceResponse,
)
async def get_preferences(
    company_id: Optional[int] = None,
    lifecycle: LifecycleService = Depends(get_lifecycle_service),
    subscriptions: SubscriptionService = Depends(get_subscription_service),
    user_id: int = Depends(RoleChecker([UserRole.SUPERADMIN, UserRole.ADMIN])),
) -> CommunicationPreferenceResponse:
    root_id = await subscriptions.resolve_company_for_billing(user_id, company_id)
    value = await lifecycle.preferences(root_id, user_id)
    return CommunicationPreferenceResponse.model_validate(value, from_attributes=True)


@router.put(
    "/preferences",
    response_model=CommunicationPreferenceResponse,
)
async def update_preferences(
    payload: CommunicationPreferenceRequest,
    lifecycle: LifecycleService = Depends(get_lifecycle_service),
    subscriptions: SubscriptionService = Depends(get_subscription_service),
    user_id: int = Depends(RoleChecker([UserRole.SUPERADMIN, UserRole.ADMIN])),
) -> CommunicationPreferenceResponse:
    root_id = await subscriptions.resolve_company_for_billing(
        user_id,
        payload.company_id,
    )
    value = await lifecycle.preferences(
        root_id,
        user_id,
        payload.billing_emails,
        payload.product_emails,
    )
    return CommunicationPreferenceResponse.model_validate(value, from_attributes=True)


@router.get("/invoices", response_model=list[BillingInvoiceResponse])
async def list_invoices(
    company_id: Optional[int] = None,
    lifecycle: LifecycleService = Depends(get_lifecycle_service),
    subscriptions: SubscriptionService = Depends(get_subscription_service),
    user_id: int = Depends(RoleChecker([UserRole.SUPERADMIN, UserRole.ADMIN])),
) -> list[BillingInvoiceResponse]:
    root_id = await subscriptions.resolve_company_for_billing(user_id, company_id)
    values = await lifecycle.invoices(root_id)
    return [
        BillingInvoiceResponse.model_validate(value, from_attributes=True)
        for value in values
    ]


@router.post("/queue/reminders", response_model=QueueResultResponse)
async def queue_reminders(
    queue_secret: str = Header(alias="X-Email-Queue-Secret"),
    service: LifecycleService = Depends(get_lifecycle_service),
) -> QueueResultResponse:
    queued = await service.queue_trial_reminders(queue_secret)
    return QueueResultResponse(queued=queued)


@router.post("/queue/process", response_model=QueueResultResponse)
async def process_queue(
    queue_secret: str = Header(alias="X-Email-Queue-Secret"),
    service: LifecycleService = Depends(get_lifecycle_service),
) -> QueueResultResponse:
    sent, failed = await service.process_queue(queue_secret)
    return QueueResultResponse(sent=sent, failed=failed)
