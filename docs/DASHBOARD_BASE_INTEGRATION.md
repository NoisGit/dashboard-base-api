# Coredeck API <-> dashboard-base Integration Contract

This document defines the minimum contract needed for the `dashboard-base` frontend to communicate with this API safely during the portfolio rebuild.

## Local backend URL

```text
http://localhost:8000/api/v1
```

## Frontend environment template

Add this to the frontend repository as `.env.local` or `.env.example`:

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_APP_NAME=Coredeck Dashboard
VITE_DEMO_EMAIL=demo@coredeck.local
VITE_DEMO_PASSWORD=1234
```

## Required backend environment for local frontend testing

The backend should expose CORS for the frontend dev server:

```env
BACKEND_CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
FRONT_URL_BASE=http://localhost:5173
```

## Auth contract

### Login

```http
POST /api/v1/auth/login
Content-Type: application/json
```

Request:

```json
{
  "email": "demo@coredeck.local",
  "password": "1234"
}
```

Expected response shape:

```json
{
  "access_token": "<jwt>",
  "refresh_token": "<jwt>",
  "token_type": "bearer"
}
```

Frontend storage expectation:

- Store `access_token` for authenticated API requests.
- Store `refresh_token` only if the frontend implements refresh flow.
- Send `Authorization: Bearer <access_token>` for protected routes.

### Current user

The frontend should expect one current-user endpoint. If the current backend keeps it under `/users/me`, use that. If the frontend expects `/auth/me`, add a compatibility alias in a small backend PR.

Preferred response shape:

```json
{
  "id": 1,
  "full_name": "Demo User",
  "email": "demo@coredeck.local",
  "role": "ADMIN",
  "company_id": null,
  "avatar": null
}
```

## Portfolio route target

Use this target route set for the new dashboard navigation. Existing backend routes can keep compatibility aliases while the refactor is in progress.

```text
POST /api/v1/auth/login
POST /api/v1/auth/logout
POST /api/v1/auth/refresh
GET  /api/v1/users/me
GET  /api/v1/users
GET  /api/v1/organizations
GET  /api/v1/workspaces
GET  /api/v1/projects
GET  /api/v1/support-tickets
GET  /api/v1/dashboard/metrics
GET  /api/v1/audit-logs
```

## Frontend changes needed in `dashboard-base`

- [ ] Centralize API URL in one client file using `import.meta.env.VITE_API_BASE_URL`.
- [ ] Replace any hardcoded API URLs.
- [ ] Replace old brand strings in page titles, sidebar, login screen, metadata, and empty states.
- [ ] Replace old roles with the final role model once the backend role refactor is merged.
- [ ] Use fake demo data and avoid screenshots/assets from previous products.
- [ ] Add a frontend README section explaining how to run against this backend.

## Backend changes still needed for full compatibility

- [ ] Confirm the current-user route used by the frontend.
- [ ] Add route aliases only after the frontend contract is confirmed.
- [ ] Add CORS parsing in settings if not already merged.
- [ ] Add seed/demo user creation for local portfolio demos.
- [ ] Add smoke tests for login, health, and current-user routes.
