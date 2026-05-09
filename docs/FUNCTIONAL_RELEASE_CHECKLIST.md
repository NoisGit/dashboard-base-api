# Coredeck Functional Release Checklist

Use this checklist before presenting Coredeck as a portfolio project.

## Backend readiness

- [ ] App boots with only `.env` variables and no code edits.
- [ ] `/health` returns a predictable response.
- [ ] `/docs` loads without import/config errors.
- [ ] Login works with a seeded demo user.
- [ ] Protected endpoints return `401` without a token.
- [ ] Protected endpoints return data with a valid token.
- [ ] CORS allows `dashboard-base` local and deployed origins.
- [ ] No real secrets exist in tracked files.
- [ ] Alembic migrations apply from an empty database.

## Frontend readiness

- [ ] `dashboard-base` reads `VITE_API_BASE_URL` from env.
- [ ] Login form calls the backend login endpoint.
- [ ] Authenticated requests include the bearer token.
- [ ] Logout clears local auth state.
- [ ] Error states do not mention old product names.
- [ ] Demo screens use fake data only.

## Portfolio readiness

- [ ] README explains the project as Coredeck, in your own words.
- [ ] Screenshots show only Coredeck branding and fake data.
- [ ] Repository has a license decision.
- [ ] Repository has no previous collaborator names or company identifiers.
- [ ] Old physical-access terminology is either removed or isolated behind compatibility aliases.
- [ ] Deployment instructions exist for backend and frontend.

## Recommended next PRs

1. Rebrand only `README.md` after its conflict is resolved.
2. Rebrand only logbook templates after their conflict is resolved.
3. Add backend CORS settings and smoke tests.
4. Add demo seed command/user.
5. Create frontend integration PR in `dashboard-base`.
6. Rename domain modules in small PRs: organizations, workspaces, activity logs, allowlists/blocklists.
