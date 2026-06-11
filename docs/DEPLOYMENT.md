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
SECRET_KEY
BACKEND_CORS_ORIGINS
FRONT_URL_BASE
```

`SECRET_KEY` must contain at least 32 characters. CORS must list explicit
frontend origins and cannot use `*`.

## Verification

After deployment:

```text
GET /health
GET /docs
```

The frontend host must be present in `BACKEND_CORS_ORIGINS`. Never run the demo
seed with a real customer credential or production data.
