# Dashboard Base API Rebrand Audit

## Goal

Transform this repository into an original backend API that works as the backend companion for `dashboard-base`.

The product identity direction is:

```text
Product name: Nois Admin
API name: Nois Admin API
Demo email: admin@nois.dev
Frontend repository: dashboard-base
Backend repository: dashboard-base-api
```

This API must move away from previous product-specific identity and become a generic admin/SaaS backend prepared for authentication, users, workspaces, projects, support tickets, dashboard metrics, audit logs, and future modules.

## Current Status

Repository:

```text
NoisGit/dashboard-base-api
```

The API already has a FastAPI structure with routers, services, models, auth utilities, database configuration, pagination, migrations and security-related dependencies.

However, it still contains old identity and business-domain references.

## High Priority Findings

### 1. README still references Sentinel Enterprise API

The current README uses:

```text
Sentinel Enterprise API
```

It also describes the API as a backend for access control, guards and administrators.

Required change:

```text
Replace README with Nois Admin API documentation.
```

Suggested sections:

```text
- Project overview
- Tech stack
- Local setup
- Environment variables
- API architecture
- Auth flow
- Main modules
- Frontend integration with dashboard-base
- Roadmap
```

### 2. main.py still references old product identity

Current app metadata includes old names and descriptions:

```text
Sentinel Enterprise API
Porteria Enterprise
```

Required new direction:

```python
app = FastAPI(
    title="Nois Admin API",
    description="Backend API for Nois Admin, a portfolio-ready admin platform.",
)
```

MCP naming should also be updated or disabled until needed.

### 3. Router set contains business-specific modules

Current router registration includes modules such as:

```text
access_logs
emergency_contacts
locations
service_contacts
whitelists
blacklists
location_logbook
```

These may still be useful technically, but the domain should be reviewed.

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

Current model exports include:

```text
Location
UserLocationAccess
CompanyLocationAccess
EmergencyContact
TypeAccessList
AccessList
ExternalPeople
AccessLog
ServiceContact
LocationLogbook
PoliceAccessPermit
```

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
1. Replace README.
2. Update FastAPI metadata in main.py.
3. Define final product/domain names.
4. Decide which old modules stay, which are renamed and which are removed.
5. Create auth contract aligned with frontend.
6. Create users contract aligned with frontend.
7. Rename Location domain to Workspace if kept.
8. Add Projects module if missing.
9. Align Support Tickets with frontend.
10. Add dashboard metrics endpoint.
11. Add deployment configuration.
12. Connect frontend to API.
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
- README no longer references old product names.
- main.py metadata is updated.
- CORS is restricted.
- Auth flow is verified.
- Environment variables are documented.
- No secrets are committed.
```
