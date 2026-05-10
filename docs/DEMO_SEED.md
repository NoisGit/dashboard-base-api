# Coredeck Demo Seed

This guide explains how to create the local demo admin user for Coredeck API.

## Demo user

```text
Email: admin@nois.dev
Role: SUPERADMIN
```

The credential itself must not be committed to the repository. The seed script expects an Argon2 hash through an environment variable.

## Required environment variables

```text
DATABASE_URL
COREDECK_DEMO_EMAIL
COREDECK_DEMO_USERNAME
COREDECK_DEMO_FULL_NAME
COREDECK_DEMO_CREDENTIAL_HASH
```

## Run seed

After setting the environment variables, run:

```bash
python scripts/seed_demo.py
```

The script is idempotent:

```text
- If the demo user does not exist, it creates it.
- If the demo user already exists, it updates the profile and credential hash.
```

## Notes

- The credential hash must be generated locally.
- The plain credential must not be committed.
- The seeded user is intended for local development and portfolio demo environments only.
