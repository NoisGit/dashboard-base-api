# Dashboard Base API Identity Audit

## Goal

Transform this repository into an original backend API that works as the backend companion for `dashboard-base`.

The product identity direction is:

```text
Product name: Coredeck
Frontend name: Coredeck Dashboard
API name: Coredeck API
Demo email: demo@coredeck.local
Demo password: 1234
Frontend repository: dashboard-base
Backend repository: dashboard-base-api
```

This API must become a generic admin/SaaS backend prepared for authentication, users, workspaces, projects, support tickets, dashboard metrics, audit logs, and future modules.

## Hard Rules

```text
No previous brand references.
No previous collaborator or legacy product references.
No old product logos.
No old product colors as identity.
No secrets committed to the repository.
```

## Current Status

Repository:

```text
personal-portfolio/dashboard-base-api
```

The API already has a FastAPI structure with routers, services, models, auth utilities, database configuration, pagination, migrations and security-related dependencies.

The remaining work is to rename old business-domain modules into Coredeck's generic domain and connect the frontend safely.

## High Priority Findings

### 1. README must use Coredeck API only

The README must stay aligned with:

```text
Coredeck API
Coredeck Dashboard
demo@coredeck.local / 1234
```

### 2. main.py metadata must use Coredeck API only

Required metadata:

```python
app = FastAPI(
    title="Coredeck API",
    description="Backend API for Coredeck, a portfolio-ready admin platform.",
)
```

MCP naming must also use Coredeck if MCP stays enabled.

### 3. Router set contains old business-specific modules

Current router registration includes modules that must be reviewed and renamed gradually.

Recommended generic module direction:

```text
access_logs -> audit/activity logs or keep only if truly needed
locations -> workspaces
emergency_contacts -> contacts or remove until needed
service_contacts -> contacts or remove until needed
whitelists -> allowlists
blacklists -> blocklists
location_logbook -> workspace_logbook or activity_notes
```

### 4. Model layer contains old domain names

Recommended target naming:

```text
Location -> Workspace
UserLocationAccess -> UserWorkspaceAccess
CompanyLocationAccess -> OrganizationWorkspaceAccess
Company -> Organization
CompanyStaff -> OrganizationStaff
EmergencyContact -> Contact
ExternalPeople -> ExternalContact / Guest / ExternalUser
AccessLog -> ActivityLog / AuditEvent
LocationLogbook -> WorkspaceLogbook
```

This must be done carefully because routers, schemas, services and migrations depend on these names.

## Recommended API Domain

Target modules:

```text
- Auth
- Users
- Organizations
- Workspaces
- Projects
- Support Tickets
- Documents
- Dashboard Metrics
- Audit Logs
- Settings
```

## Recommended Endpoint Direction

Frontend and backend should align around these endpoints:

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

## Security Requirements

Required backend security work:

```text
- Password hashing with Argon2.
- Access token and refresh token flow.
- Role-based route protection.
- CORS restricted by environment.
- Environment variable validation.
- Safe error responses.
- Audit logging for sensitive actions.
- Avoid secrets in repository.
```

## Suggested Work Order

```text
1. Create develop branch.
2. Confirm identity cleanup.
3. Harden CORS and settings.
4. Create auth contract aligned with frontend.
5. Create users contract aligned with frontend.
6. Rename Location domain to Workspace if kept.
7. Add Projects module if missing.
8. Align Support Tickets with frontend.
9. Add dashboard metrics endpoint.
10. Add deployment configuration.
11. Connect frontend to API.
```

## Migration Warning

Do not mass-rename models without planning.

Recommended approach:

```text
1. Rename one module at a time.
2. Update model, schema, service and router together.
3. Run tests/build after each module.
4. Keep compatibility aliases temporarily if needed.
```

## Deployment Rule

Do not deploy this API publicly until:

```text
- README uses Coredeck only.
- main.py metadata uses Coredeck only.
- CORS is restricted.
- Auth flow is verified.
- Environment variables are documented.
- No secrets are committed.
```
