# Nois Admin API

Nois Admin API is the backend service for the Nois Admin dashboard.

It is built with FastAPI, SQLModel, SQLAlchemy async, Pydantic, JWT authentication and role-based access patterns.

## Project Status

This API is in active cleanup and rebuild mode.

Current goals:

- Remove all previous product identity.
- Keep the backend aligned with `dashboard-base`.
- Provide secure authentication for the frontend.
- Expose typed and predictable API modules.
- Prepare the project for portfolio usage and future deployment.

## Product Identity

```text
Product: Nois Admin
API: Nois Admin API
Demo email: admin@nois.dev
Frontend repository: dashboard-base
Backend repository: dashboard-base-api
```

## Planned Modules

```text
- Auth
- Users
- Organizations
- Workspaces
- Projects
- Support Tickets
- Dashboard Metrics
- Audit Logs
- Settings
```

## Project Structure

```text
dashboard-base-api
├── src
│   ├── main.py
│   ├── api
│   ├── auth
│   ├── config
│   ├── core
│   ├── database
│   ├── models
│   ├── routers
│   ├── schemas
│   └── services
├── requirements.txt
└── README.md
```

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

Create a `.env` file:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/nois_admin
JWT_SECRET_KEY=change-me
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
BACKEND_CORS_ORIGINS=http://localhost:5173
```

Run the API:

```bash
uvicorn src.main:app --reload --host 127.0.0.1 --port 8000
```

Open API docs:

```text
http://127.0.0.1:8000/docs
```

## Frontend Integration

The frontend repository should consume this API from:

```text
http://localhost:8000/api/v1
```

Expected frontend environment variable:

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

## Planned API Contract

```text
POST /api/v1/auth/login
POST /api/v1/auth/logout
POST /api/v1/auth/refresh
GET  /api/v1/auth/me
GET  /api/v1/users
GET  /api/v1/organizations
GET  /api/v1/workspaces
GET  /api/v1/projects
GET  /api/v1/support-tickets
GET  /api/v1/dashboard/metrics
GET  /api/v1/audit-logs
```

## Security Roadmap

- Password hashing with Argon2.
- Access and refresh token flow.
- Role-based route protection.
- Environment-based CORS.
- Safe error responses.
- Audit logs for sensitive actions.
- No secrets committed to the repository.

## Repository Workflow

```text
feature branches → develop → main
```

## Author

Developed by NoisGit.
