# Locentr SaaS Readiness

This document separates portfolio demo readiness from commercial SaaS
readiness. A feature is not considered complete only because a model or route
name exists.

## Open Issue Audit

| Issue | Status | Current evidence | Remaining work |
|---|---|---|---|
| #4 Security settings and errors | Keep open | Production secrets, explicit CORS, HTTP limits, headers and safe health responses are enforced. | Define one backward-compatible error envelope and add global exception contract tests. |
| #12 Free deployment | Keep open | `docs/DEPLOYMENT.md` defines the commands and recommended topology. | Create the public API, configure environment variables and verify frontend-to-backend calls. |
| #15 Database and migrations | Ready to close | Runtime and seed no longer call `create_all`; clean and existing PostgreSQL upgrades pass; Alembic reports no drift. | No code work remains. Provider provisioning belongs to #12. |
| #17 Frontend response contract | Keep open | CORS, pagination and real route groups are aligned with the dashboard. | Standardize success/error wrappers only through a documented versioned migration. |
| #25 Security hardening | Keep open | ORM queries, input bounds, tenant policies, token hardening and 30 regressions are present. | Private storage, deployed integration tests and broader malicious-input coverage remain. |

## P0 Before A Public Demo

1. Deploy the API and persistent PostgreSQL database, run
   `alembic upgrade head`, then verify `/health`, `/docs`, login, refresh and
   one location workflow from the deployed dashboard.
2. Replace public document/media URLs with private storage and short-lived
   signed upload/read URLs. Until then, use synthetic demo files only and do
   not present Documents as suitable for customer-confidential data.
3. Configure and test the real SMTP sender if password recovery is enabled in
   the public demo.
4. Use production-only secrets, explicit CORS origins and a proxy/platform
   providing TLS, HSTS, distributed rate limiting and logs.

With synthetic data and document uploads disabled, the operations workflow can
be shown safely while private storage is completed.

## P1 Portfolio Professionalization

- Standard error response with `detail`, `code` and `request_id`.
- Integration tests against PostgreSQL for tenant boundaries and token races.
- Deployed smoke tests for dashboard, API, database and storage.
- Audit events for authentication, company, user, location and document
  mutations.
- Backup/restore drill, retention policy and basic observability alerts.
- Invitations instead of sharing generated credentials with company users.
- Optional MFA for `SUPERADMIN` and company administrators.

## Plans And 14-Day Trial

Plans and a 14-day trial are expected for a commercially sellable SaaS, but
they are not required to demonstrate the core Locentr operations product.
They should be added after the current backend and dashboard flows are deployed
and coherent.

The existing `Plan` model and `users.plan_id` are not enough. A subscription is
owned by a company tenant, not by each user.

Recommended backend model:

```text
Plan
├── code
├── name
├── limits: locations, admins, operators, daily reads, storage
└── feature flags

CompanySubscription
├── company_id (unique)
├── plan_id
├── status: trialing, active, past_due, canceled
├── trial_started_at
├── trial_ends_at
├── current_period_start/current_period_end
└── billing provider customer/subscription IDs

UsageCounter
├── company_id
├── metric
├── period
└── quantity
```

Backend tasks:

- Move plan ownership from users to the root company subscription.
- Create a 14-day trial when a tenant is onboarded.
- Enforce entitlements in services before creating locations, admins and
  operators or exceeding usage limits.
- Add idempotent checkout/webhook handling only after choosing a billing
  provider.
- Add scheduled trial-expiration and payment-state reconciliation.
- Record subscription and entitlement changes in the audit log.

Frontend tasks:

- Pricing and plan comparison page.
- Trial countdown and usage indicators.
- Billing/settings page for the company administrator.
- Upgrade, checkout success/cancel and payment-problem states.
- Clear disabled states when a plan limit is reached.
- Tenant onboarding flow for company, first admin and first location.

## Later Product Ideas

- Company invitations with expiring one-time links.
- CSV import job status and downloadable error reports.
- Scheduled document expiration reminders.
- Custom notification preferences by user and location.
- Read-only auditor role only if the business explicitly approves a new role.
- Exportable compliance reports for access logs and location logbooks.

New roles, modules or endpoints require a product decision and frontend
contract first.
