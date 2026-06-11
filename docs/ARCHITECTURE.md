# Locentr Architecture

Locentr is a multi-tenant operations SaaS organized around companies and
physical locations.

## Domain

```text
Platform
└── Company
    ├── Subcompanies
    ├── Users
    ├── Locations
    │   ├── Assigned operators
    │   ├── Access lists and access logs
    │   ├── Custom forms
    │   └── Location logbook
    ├── Documents
    └── Support tickets
```

`Location` is the canonical operational unit. `Workspace`, `Organization`,
and `Project` are not API resources.

## Roles And Tenant Boundaries

| Role | Scope |
|---|---|
| `SUPERADMIN` | All companies and locations. Created and managed outside public API endpoints. |
| `ADMIN` | Own company, direct subcompanies, their users, documents and locations. |
| `OPERATOR` | Only explicitly assigned locations. |
| `CLIENT` | Read or operational access granted through its company and location policies. |

Router role checks are only the first gate. Services must call the centralized
company or location policy before reading or mutating an object.

## API Conventions

- Public API prefix: `/api/v1`.
- Resource names and URL segments are English.
- User-facing content and validation messages consumed by the dashboard may be Spanish.
- SQLModel/SQLAlchemy expressions are required; raw SQL built from request data is forbidden.
- IDs remain transport identifiers. The frontend decides whether they are displayed.
