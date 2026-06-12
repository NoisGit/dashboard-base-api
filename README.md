# Locentr API

Locentr API is the FastAPI backend for a portfolio SaaS operations dashboard.

Locentr is centered around companies, subcompanies, locations, access management, documents, support tickets, notifications and audit logs.

## Project Status

This repository contains the active Locentr enterprise backend. It includes tenant-aware
operations, a 14-day trial, subscription plans, Stripe lifecycle hooks, team invitations,
transactional email delivery and a reproducible portfolio dataset.

## Product Direction

Locentr is a multi-company, multi-location operations dashboard.

The current domain model is:

```text
Company
├── Subcompanies
├── Users
├── Locations
│   ├── Operators
│   ├── Access lists
│   ├── Access logs
│   ├── Custom forms
│   ├── Emergency contacts
│   ├── Service contacts
│   └── Location logbook
├── Documents
├── Team invitations and plan seats
├── Subscription, invoices and communication preferences
├── Support tickets
├── Notifications
└── Audit log
```

### Important domain decision

`Workspaces` are **not** an active backend module.

The previous workspace idea is consolidated into `Locations`. New frontend and backend work should use:

```text
Frontend: Locations
Backend:  /api/v1/locations
```

Do not add a new `/workspaces` API unless the product architecture is explicitly changed later.

## Roles

Current roles are defined as string enum values:

```text
SUPERADMIN
ADMIN
OPERATOR
CLIENT
```

General intent:

| Role | Purpose |
|---|---|
| SUPERADMIN | Platform-level administration. |
| ADMIN | Company/subcompany/location administration. |
| OPERATOR | Operational access to assigned locations. |
| CLIENT | Read or limited access to company/location data. |

Permissions must still be enforced at service/object level, not only at router level.

## Current API Modules

Routers are registered under `/api/v1`.

| Module | Route group | Status | Notes |
|---|---|---|---|
| Auth | `/auth` | Active | Login, operator login, refresh, me, logout, password recovery. |
| Users | `/users` | Active | User CRUD, filters, suspend, password change. |
| Companies | `/companies` | Active | Companies, subcompanies and user assignment. |
| Locations | `/locations` | Active | Main operational unit. Replaces the old workspace concept. |
| Access Logs | `/access-logs` | Active | Entry/exit and dashboard access activity. |
| Whitelists | `/whitelists` | Active | Allowed access list entries. |
| Blacklists | `/blacklists` | Active | Denied access list entries. |
| Documents | `/documents` | Active | Metadata for company/location files. |
| Storage | `/storage` | Infrastructure | File/storage support layer. |
| Support Tickets | `/support-tickets` | Active | Support workflow with statuses and comments. |
| Notifications | `/notifications` | Active | Unread list, ownership-safe read state and platform broadcasts. |
| Audit Log | `/audit-log` | Active | Security and system activity history. |
| Dashboard | `/dashboard` | Active | Location-aware dashboard stats. |
| System | `/system` | Internal | Platform/system stats for SUPERADMIN. |
| Emergency Contacts | `/emergency-contacts` | Optional | Location-scoped contacts. |
| Service Contacts | `/service-contacts` | Optional | Location-scoped service providers. |
| Location Logbook | `/location-logbook` | Optional | Location-scoped operational logbook. |
| Teams | `/teams` | Active | Invitations, acceptance, revoke/resend and seat usage. |
| Lifecycle | `/lifecycle` | Active | Verification, invoices, preferences and queued email jobs. |
| Subscriptions | `/subscriptions` | Active | Plans, 14-day trial, checkout, portal and Stripe webhooks. |

## Removed or Postponed Concepts

These concepts should not guide current implementation:

```text
Organizations
Workspaces
Projects
Settings as a standalone product module
Legacy mailbox/email templates
Old productos anteriores/Azure/product references
```

If any of these return later, they need a new architecture decision and API contract first.

## Tech Stack

| Area | Technology |
|---|---|
| API | FastAPI |
| Data Models | SQLModel / SQLAlchemy async |
| Validation | Pydantic |
| Auth | JWT |
| Pagination | fastapi-pagination |
| Migrations | Alembic |
| Database | PostgreSQL-compatible SQLAlchemy URL |
| Storage | Provider-neutral public storage URL and bucket config |

## Local Setup

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create `.env` from `.env.example`, then start a clean PostgreSQL instance:

```bash
cp .env.example .env
docker compose up -d --wait locentr-db
alembic upgrade head
```

Production must provide safe values for `SECRET_KEY` and `DATABASE_URL`.

Create the optional portfolio dataset. Generate the hash at runtime; never commit the demo
password or its hash:

```bash
PYTHONPATH=. \
LOCENTR_DEMO_CREDENTIAL_HASH="$(python -c \
'from argon2 import PasswordHasher; print(PasswordHasher().hash("choose-a-local-password"))')" \
python scripts/seed_demo.py
```

Run the API:

```bash
uvicorn src.main:app --reload --host 127.0.0.1 --port 8000
```

See `docs/DEPLOYMENT.md` for local and portfolio deployment commands.

Open API docs:

```text
http://127.0.0.1:8000/docs
```

## Frontend Integration

Frontend repository:

```text
https://github.com/NoisGit/locentr-dashboard
```

The frontend should point to the backend host. Frontend services already include `/api/v1` in their endpoint URLs.

Local frontend environment:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_ENABLE_MOCK=false
```

Example service URL produced by the frontend:

```text
http://localhost:8000/api/v1/locations/
```

## Current Frontend Contract Direction

Use these route groups as the active backend contract:

```text
POST /api/v1/auth/login
POST /api/v1/auth/operator-login
GET  /api/v1/auth/me
POST /api/v1/auth/refresh
POST /api/v1/auth/logout

GET  /api/v1/users/
POST /api/v1/users/
GET  /api/v1/users/{user_id}
PUT  /api/v1/users/{user_id}

GET  /api/v1/companies/
POST /api/v1/companies/
POST /api/v1/companies/subcompany
POST /api/v1/companies/{company_id}/users
POST /api/v1/companies/{company_id}/create-users

GET  /api/v1/locations/
POST /api/v1/locations/
GET  /api/v1/locations/{location_id}
PUT  /api/v1/locations/{location_id}
DELETE /api/v1/locations/{location_id}

GET  /api/v1/dashboard/location/{location_id}
GET  /api/v1/teams/invitations
GET  /api/v1/teams/seats
GET  /api/v1/lifecycle/invoices
GET  /api/v1/lifecycle/preferences
GET  /api/v1/subscriptions/plans
GET  /api/v1/subscriptions/me
GET  /api/v1/support-tickets/
GET  /api/v1/audit-log/
```

For a complete source of truth, use FastAPI OpenAPI docs from the running API.

## Security Baseline

- Centralized settings for secrets and token expiration.
- Required production secret/database configuration.
- JWT authentication and refresh flow.
- Role-aware route protection.
- Environment-based CORS.
- No committed `.env` files or real production secrets.
- Central company/location object authorization.
- Authentication rate limits and request body limits.
- Security headers and request IDs.
- Hashed password-reset and one-time police-access tokens.
- Upload type and size allowlists.
- Hashed, expiring and single-use invitation and verification tokens.
- Idempotent billing/email events and retryable delivery records.
- Versioned API error envelope with request IDs and private internal failures.

See `docs/SECURITY.md` for application and infrastructure responsibilities.
See `docs/SAAS_READINESS.md` for demo blockers and the plans/trial roadmap.

## Documentation

- `docs/ARCHITECTURE.md`
- `docs/FRONTEND_CONTRACT.md`
- `docs/SECURITY.md`
- `docs/DEMO_SEED.md`

## Ownership

Independent portfolio project prepared for a personal GitHub portfolio.
