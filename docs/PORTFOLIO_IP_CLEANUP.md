# Coredeck Portfolio & IP Cleanup Plan

> This is an engineering checklist, not legal advice. If ownership or past employment agreements are unclear, validate the repository with a qualified attorney before publishing it publicly.

## Goal

Make this repository safe to present as an independent portfolio project by reducing visible legacy identity, documenting ownership boundaries, and separating the new Coredeck product direction from any previous team or client context.

## Current risk areas to clean before public launch

The repository still contains legacy business-domain concepts that can make the project look tied to the previous product domain even when the code is yours:

- `janitor` / `JANITOR` role names.
- `police` access/logbook naming.
- `locations` as a physical-access concept instead of a generic `workspace` concept.
- `whitelist` / `blacklist` naming that should become `allowlist` / `blocklist`.
- `company` naming that should become `organization`.
- Spanish copy that references concierge/physical access workflows.
- Historical migration names and columns from the old domain.

## Safe cleanup sequence

Avoid one giant rename PR. Use small pull requests so conflicts are manageable.

### Phase 1: visible identity only

- [x] Remove old product branding from local env and Docker defaults.
- [x] Update basic API identity strings.
- [x] Update reset-password email branding.
- [ ] Rebrand `README.md` after the current conflict is merged.
- [ ] Rebrand `src/templates/logbook/police_error.html` after the current conflict is merged.

### Phase 2: public contract with the frontend

- [ ] Publish a stable API contract for `dashboard-base`.
- [ ] Add a frontend `.env` template for `VITE_API_BASE_URL`.
- [ ] Align auth response shape with frontend expectations.
- [ ] Confirm CORS allows the frontend origin in local and deployed environments.

### Phase 3: domain rename without breaking the DB

- [ ] `Company` -> `Organization`.
- [ ] `Location` -> `Workspace`.
- [ ] `JANITOR` -> `AGENT` or another platform-specific role.
- [ ] `AccessLog` -> `ActivityLog`.
- [ ] `Whitelist` -> `Allowlist`.
- [ ] `Blacklist` -> `Blocklist`.
- [ ] `PoliceAccessPermit` -> `ShareLink` or `ReadOnlyAccessPermit`.

### Phase 4: migration strategy

- [ ] Create additive migrations first: new columns/tables/enum values.
- [ ] Backfill data.
- [ ] Keep compatibility aliases for one frontend release.
- [ ] Remove legacy names in a later major cleanup.

### Phase 5: provenance and licensing

- [ ] Add a root `LICENSE` once you choose how the portfolio repo may be reused.
- [ ] Add a `NOTICE.md` documenting that Coredeck is an independent portfolio rebuild.
- [ ] Ensure no real customer/company names, emails, keys, logos, screenshots, or database dumps are committed.
- [ ] Keep a private record of your own authorship history and commits.

## Practical anti-plagiarism checklist

Before making the repo public, verify:

- [ ] No previous coworker names or personal identifiers appear in docs, comments, examples, seed data, assets, or commit-added files.
- [ ] No old product names remain in public docs/templates.
- [ ] No copied logos, colors, screenshots, or exact marketing copy from another product remain.
- [ ] The README explains the new product idea in your own words.
- [ ] The API routes and domain names tell a generic SaaS/admin story, not the old physical-access story.
- [ ] All secrets are placeholders or environment variables.
- [ ] The frontend and backend demo use fake data only.

## Legal context to remember

Copyright generally protects original works of authorship, including computer programs, once fixed in a tangible form. A public GitHub repository should also have an explicit license if you want to define reuse permissions. If there is any doubt about employment contracts, client ownership, or third-party code, get legal review before publishing.

## Reference links

- U.S. Copyright Office: https://www.copyright.gov/what-is-copyright/
- U.S. Copyright Office computer programs: https://www.copyright.gov/register/tx-programs.html
- GitHub Docs on repository licensing: https://docs.github.com/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository
