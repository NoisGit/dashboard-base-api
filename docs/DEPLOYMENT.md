# Locentr API Deployment

Alembic is the only supported database schema workflow. The API and demo seed
never create tables automatically.

## Local Database

Start PostgreSQL:

```bash
docker compose up -d locentr-db
```

Set `DATABASE_URL`, then create or upgrade the schema:

```bash
alembic upgrade head
```

Seed the optional demo account only after migrations:

```bash
python scripts/seed_demo.py
```

Start the API:

```bash
uvicorn src.main:app --reload --host 127.0.0.1 --port 8000
```

## Portfolio Deployment

Recommended low-cost portfolio setup:

- Render free web service for the FastAPI process.
- Neon Free Postgres for a persistent demo database.
- A separate private object-storage bucket before enabling real documents.

Render's free Postgres databases expire after 30 days, so they are not the
recommended persistent database for this demo. Free service limits can change;
verify provider terms before deployment.

Build command:

```bash
pip install -r requirements.txt
```

Pre-deploy command:

```bash
alembic upgrade head
```

Start command:

```bash
uvicorn src.main:app --host 0.0.0.0 --port $PORT
```

Required production variables:

```text
ENV=production
DATABASE_URL
DB_POOL_SIZE
DB_MAX_OVERFLOW
DB_POOL_TIMEOUT_SECONDS
DB_POOL_RECYCLE_SECONDS
DB_STATEMENT_TIMEOUT_MS
SECRET_KEY
BACKEND_CORS_ORIGINS
FRONT_URL_BASE
BACKEND_PUBLIC_BASE_URL
PRIVATE_STORAGE_ROOT
STORAGE_SIGNED_URL_EXPIRE_SECONDS
TRIAL_DAYS
TRIAL_PLAN_CODE
STRIPE_SECRET_KEY
STRIPE_WEBHOOK_SECRET
STRIPE_PRICE_STARTER
STRIPE_PRICE_GROWTH
STRIPE_PRICE_SCALE
BILLING_RECONCILIATION_SECRET
MAX_CONCURRENT_REQUESTS
SLOW_REQUEST_THRESHOLD_MS
```

`SECRET_KEY` must contain at least 32 characters. CORS must list explicit
frontend origins and cannot use `*`.

Size the database pool together with the number of API workers. The maximum
possible PostgreSQL connections per instance is approximately
`workers * (DB_POOL_SIZE + DB_MAX_OVERFLOW)`. Keep that total below the
provider limit. `DB_STATEMENT_TIMEOUT_MS` cancels runaway queries, while
`MAX_CONCURRENT_REQUESTS` rejects excess work with `503` and `Retry-After`
instead of allowing an unbounded queue.

## Verification

After deployment:

```text
GET /live
GET /ready
GET /docs
```

`/live` checks the process only. `/ready` and `/health` check PostgreSQL and
return `503` while the service cannot safely receive traffic.

The frontend host must be present in `BACKEND_CORS_ORIGINS`. Never run the demo
seed with a real customer credential or production data.

`PRIVATE_STORAGE_ROOT` must use persistent storage readable and writable only
by the API process. Private document upload and read URLs are tenant-bound and
expire after `STORAGE_SIGNED_URL_EXPIRE_SECONDS`.

Stripe must send subscription events to
`/api/v1/subscriptions/stripe/webhook`. A scheduler should call
`/api/v1/subscriptions/reconcile` with `X-Reconciliation-Secret` at least once
per day.
