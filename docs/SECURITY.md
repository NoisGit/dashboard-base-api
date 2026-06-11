# Locentr Security Baseline

The backend follows an OWASP-oriented baseline:

- Argon2 password hashing and JWT access/refresh token type checks.
- Password recovery responses do not reveal whether an account exists.
- Reset and police-access secrets are stored as SHA-256 digests.
- Central object authorization for company and location resources.
- Explicit operator-to-location assignments.
- ORM query construction instead of request-built SQL.
- Pydantic length, format, size, and enum validation.
- CSV extension, MIME, UTF-8, header, and 5 MB size checks.
- Upload extension/content-type allowlists by storage container.
- Request body limits, authentication rate limits, request IDs, and secure headers.
- CORS origins supplied through environment configuration.
- Production startup rejects development secrets and missing database configuration.

## Deployment Controls

Application rate limiting is per process and is defense in depth. Production
must also use a reverse proxy or managed WAF/CDN for:

- Distributed rate limiting and bot management.
- TLS termination and HSTS.
- Maximum body size enforcement, including chunked requests.
- Connection, header, and request timeouts.
- IP reputation, geographic rules, and volumetric DDoS protection.
- Central logs, metrics, alerts, and request-ID correlation.

Recommended checks in CI include `ruff`, `pytest`, `pip-audit`, and `bandit`.
Database roles should use least privilege and production backups must be tested.
