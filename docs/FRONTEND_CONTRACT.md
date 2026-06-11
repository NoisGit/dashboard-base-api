# Locentr Frontend Contract

The dashboard uses `VITE_API_BASE_URL` as the host and calls endpoints under
`/api/v1`.

Verified route groups:

| Frontend area | Backend route |
|---|---|
| Authentication | `/api/v1/auth` |
| Users | `/api/v1/users` |
| Companies | `/api/v1/companies` |
| Locations | `/api/v1/locations` |
| Dashboard metrics | `/api/v1/dashboard/location/{location_id}` |
| Access management | `/api/v1/whitelists`, `/blacklists`, `/access-logs` |
| Documents | `/api/v1/documents` |
| Support tickets | `/api/v1/support-tickets` |
| Notifications | `/api/v1/notifications` |
| Logbook | `/api/v1/location-logbook` |
| Audit | `/api/v1/audit-log` |

Important contracts:

- Company `name`, `id_number`, and `type_document` are required.
- A location has no required logo.
- Public API endpoints cannot create, assign, suspend, or delete `SUPERADMIN`.
- Operator usernames created by bulk import receive the login email
  `{username}@locentr.com`.
- Police logbook links expire after 30 minutes and are invalidated after the
  first successful view.
- Document operations validate company ownership for `ADMIN`.
- Notification read operations validate notification ownership.

OpenAPI at `/docs` is the machine-readable source of truth.
