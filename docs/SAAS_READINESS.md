# Locentr SaaS Readiness

Locentr now includes the operational product and the commercial foundation
needed for a portfolio SaaS. Production readiness still depends on deployment
configuration and external provider credentials.

## Issue Audit

| Issue | Status | Resolution |
|---|---|---|
| #4 Coredeck security | Closed, obsolete | Safe CORS, secrets, HTTP controls and error privacy are implemented. The remaining versioned error-envelope work is Locentr issue #33. |
| #12 Coredeck free deployment | Closed, obsolete | Replaced by Locentr production-like deployment issue #34. |
| #15 Database and migrations | Closed | Alembic is the only schema source and clean upgrades pass. |
| #17 Coredeck response contract | Closed, obsolete | Current dashboard contracts are aligned; future error normalization is isolated in #33. |
| #25 Security hardening | Closed | ORM safety, tenant authorization, token hardening, input limits and security tooling are verified. |
| #31 Private storage | Completed | Documents use company-bound signed upload/read URLs and trusted replacement/deletion. |
| #32 Plans and trial | Completed | Company subscriptions, self-service onboarding, 14-day trial, limits and Stripe integration are implemented. |

## Implemented SaaS Layer

- Subscription ownership belongs to the root `Company`.
- Exactly one `CompanySubscription` exists per root tenant.
- Self-service onboarding creates the company, first `ADMIN`, first location and
  a 14-day Growth trial in one transaction.
- A unique root company identifier prevents repeated trials for the same
  company.
- Plan limits cover locations, administrators, operators, daily access reads
  and private storage.
- Service methods enforce limits while locking the subscription row.
- Trial expiration can happen lazily during requests and through the protected
  `/api/v1/subscriptions/reconcile` scheduled endpoint.
- Stripe Checkout preserves remaining trial time.
- Stripe webhook signatures use the raw request body and processed event IDs
  are unique, making retries idempotent.
- Subscription cancellation and payment failures revoke provisioning access.
- The dashboard includes pricing, onboarding, trial countdown, usage,
  checkout states and billing portal access.

## Required Stripe Configuration

```text
STRIPE_SECRET_KEY
STRIPE_WEBHOOK_SECRET
STRIPE_PRICE_STARTER
STRIPE_PRICE_GROWTH
STRIPE_PRICE_SCALE
BILLING_RECONCILIATION_SECRET
```

Register the webhook route:

```text
POST /api/v1/subscriptions/stripe/webhook
```

Schedule the reconciliation route with:

```text
POST /api/v1/subscriptions/reconcile
X-Reconciliation-Secret: <BILLING_RECONCILIATION_SECRET>
```

## Remaining P0 Before Public Launch

1. Complete issue #34: deploy API, PostgreSQL and persistent private storage.
2. Configure Stripe test/live products, Price IDs and webhook secret.
3. Configure and verify the SMTP sender used by password recovery.
4. Run a deployed smoke test for onboarding, login, upload, checkout and
   webhook reconciliation.
5. Configure backups, TLS/HSTS, distributed rate limiting, logs and alerts.

## P1 Professionalization

- Complete issue #33 with a versioned error envelope containing `code`,
  `message`, `details` and `request_id`.
- Add invitations and email verification before allowing production tenant
  onboarding.
- Add MFA for `SUPERADMIN` and company administrators.
- Emit dedicated audit events for subscription and entitlement changes.
- Add retention rules and scheduled cleanup for abandoned uploads.
- Add provider-backed object storage when deploying more than one API replica.

## Verdict

The application is feature-complete for a local portfolio SaaS demo. It must
not be called production-ready until the external services and deployment
controls above are configured and tested.
