# Coredeck API

Coredeck API is the backend service for Coredeck Dashboard.

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
Product: Coredeck
Frontend: Coredeck Dashboard
Backend: Coredeck API
Demo email: demo@coredeck.local
Demo password: 1234
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


## Portfolio Focus

Coredeck API is presented as an independent portfolio backend that demonstrates:

- Modular FastAPI architecture with routers, schemas, services and models.
- JWT authentication and role-aware access patterns.
- Async database access with SQLModel/SQLAlchemy.
- Migration-based schema evolution with Alembic.
- Docker-based local database setup.
- Clear environment configuration without committed production secrets.

See `docs/PORTFOLIO_TASKS.md` for the current rebrand and refactor roadmap.
See `docs/GITHUB_WORKFLOW.md` for the GitHub commit and pull request workflow.

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

Create a `.env` file based on `.env.example`.

Required environment variables:

```text
DATABASE_URL
SECRET_KEY
ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS
BACKEND_CORS_ORIGINS
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

```text
VITE_API_BASE_URL
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

## Ownership

Independent portfolio project prepared for a personal GitHub portfolio.
