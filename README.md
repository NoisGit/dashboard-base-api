# Locentr API

Locentr API is the FastAPI backend for a portfolio SaaS operations dashboard.

Locentr is centered around companies, subcompanies, locations, access management, documents, support tickets, notifications and audit logs.

## Project Status

This repository is in active cleanup and rebuild mode.

Current goals:

- Keep the backend aligned with `locentr-dashboard`.
- Remove obsolete template/product references.
- Expose typed and predictable API modules.
- Keep secrets and deployment configuration out of source control.
- Prepare a clean portfolio-ready SaaS backend.

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

Create a virtual environment:

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

Activate it on macOS/Linux:

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file from `.env.example` when available.

Required or commonly used environment variables:

```env
ENV=dev
DEBUG=true
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/locentr
SECRET_KEY=change-me
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
BACKEND_CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
FRONT_URL_BASE=http://localhost:5173
STORAGE_PUBLIC_BASE_URL=http://localhost:54321/storage/v1/object/public/locentr
STORAGE_BUCKET_NAME=locentr
```

Production must provide safe values for `SECRET_KEY` and `DATABASE_URL`.

Run the API:

```bash
uvicorn src.main:app --reload --host 127.0.0.1 --port 8000
```

Apply database migrations before starting the API or running the demo seed:

```bash
alembic upgrade head
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

See `docs/SECURITY.md` for application and infrastructure responsibilities.

## Documentation

- `docs/ARCHITECTURE.md`
- `docs/FRONTEND_CONTRACT.md`
- `docs/SECURITY.md`
- `docs/DEMO_SEED.md`

## Ownership

Independent portfolio project prepared for a personal GitHub portfolio.
