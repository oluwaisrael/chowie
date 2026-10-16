# Deployment

No public production deployment has been performed. GitHub delivery and local verification do not establish production readiness.

## Local containers

Requires Docker Engine running and Docker Compose v2:

```sh
cp .env.example .env
docker compose up --build -d
docker compose run --rm api uv run --no-sync python -m oriade.cli seed
docker compose run --rm api uv run --no-sync python -m oriade.cli create-admin --email you@example.com
```

Visit `http://localhost:3000`. The seed is sample catalog data only. Replace sample prices, zones, pickup address and generated imagery before public ordering. The migration service must finish before API and worker start. Compose uses a single beat scheduler; separate scheduler and workers in production.

## Native development

Requires Node 24, pnpm 11.11.0, Python 3.12–3.14, uv 0.13.1, PostgreSQL and Redis. Copy `.env.example`, then set DATABASE_URL, REDIS_URL and APP_ORIGIN for the local services. `APP_ORIGIN` must exactly match the browser origin, including port.

```sh
pnpm install --frozen-lockfile
cd apps/api
uv sync --frozen
uv run alembic upgrade head
uv run python -m oriade.cli seed
uv run python -m oriade.cli create-admin --email you@example.com
uv run uvicorn oriade.main:app --host 127.0.0.1 --port 8000
```

In a second terminal at repository root:

```sh
pnpm dev
```

In a third terminal:

```sh
cd apps/api
uv run celery -A oriade.workers.tasks worker --beat --loglevel=INFO --schedule=/tmp/oriade-beat
```

For a different frontend port, run `pnpm --filter @oriade/storefront dev --port 3001` and change APP_ORIGIN to `http://localhost:3001`. For an API on another host, set API_INTERNAL_URL in the frontend process; Next.js rewrites embed this destination during production builds.

## Production topology

Use the provided web/API Dockerfiles behind HTTPS, managed PostgreSQL, private Redis, object storage and SMTP. Set `ENVIRONMENT=production`, the exact HTTPS APP_ORIGIN, a strong database password, and secrets through the deployment secret manager. Do not expose PostgreSQL or Redis to the internet. Preserve streaming responses at the ingress: disable buffering on `/api/events` and allow long-lived connections. Configure body-size limits and edge rate limiting.

Run migrations as a single release job. Deploy web with API_INTERNAL_URL pointing to the private API service. Use a dedicated worker and exactly one Celery beat scheduler. Configure Sentry DSN if desired; OpenTelemetry FastAPI hooks require an SDK/exporter/collector setup before traces reach a backend. Monitor outbox backlog, database connection usage, 5xx responses, failed reset emails and stock reservations.

Keep database backups with point-in-time recovery and run a restore drill. The `/health` endpoint checks PostgreSQL; add Redis/worker-specific checks in infrastructure. Compose is development-oriented and does not provide TLS, production secret management or high availability.

## Integration activation

- **Photography:** configure S3_BUCKET, S3_PUBLIC_URL, optional S3_ENDPOINT_URL, region and AWS credentials with write permissions limited to the menu prefix.
- **Reset email:** configure SMTP_HOST, SMTP_PORT, SMTP_FROM and authentication. STARTTLS is required. Verify delivery and sender DNS.
- **WhatsApp:** default number is 2348066514361. Click-to-chat requires no API credentials. There is no automatic outbound Cloud API integration.

## Tests

Create separate databases named `oriade_test` and `oriade_e2e`; never point tests at business data.

```sh
cd apps/api
TEST_DATABASE_URL=postgresql+psycopg://USER:PASSWORD@localhost/oriade_test \
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@localhost/oriade_test uv run alembic upgrade head
TEST_DATABASE_URL=postgresql+psycopg://USER:PASSWORD@localhost/oriade_test \
TEST_REDIS_URL=redis://localhost:6379/15 uv run pytest -q
```

The API suite truncates its dedicated `_test` database and flushes its dedicated Redis database 15. Use isolated test services.

For browser tests, migrate an `_e2e` database, run `tests/seed_e2e.py` with DATABASE_URL pointing to it, and start the API against that database. Run the web app, install Chromium with `pnpm --filter @oriade/storefront exec playwright install chromium`, then run `E2E_BASE_URL=http://localhost:3000 pnpm test:e2e`. Alternatively set PLAYWRIGHT_CHROMIUM_PATH to an existing Chrome executable. Browser tests never click the external WhatsApp destination or send a message.
