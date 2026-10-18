# Óriade

Óriade is a premium Nigerian food ordering experience: browse a live menu, customize a meal, save an order, and hand it off to the restaurant through WhatsApp for confirmation.

![Óriade homepage](docs/screenshots/home-desktop.png)

## What works

- Responsive homepage, menu, meal details, bag, checkout, account, and order tracking.
- Guest or signed-in checkout with server-side prices, stock checks, delivery zones, and idempotency.
- PostgreSQL-backed orders with status history and secure guest access tokens.
- WhatsApp click-to-chat handoff to `+234 806 651 4361`; opening WhatsApp never confirms an order automatically.
- Staff operations: login, order confirmation, kitchen queue, status updates, menu availability, staff management, and basic reports.

## Stack

Next.js 16, React 19, TypeScript, FastAPI, SQLAlchemy, Alembic, PostgreSQL, Redis, and Playwright.

The API is a modular monolith. The storefront reads catalog data from FastAPI, while checkout totals and order state are authoritative in PostgreSQL.

## Run locally

1. Copy `.env.example` to `.env` and adjust values only if your local services use different ports.
2. Start PostgreSQL and Redis, or use the supplied Compose file:

   ```bash
   docker compose up -d db redis
   ```

3. Install dependencies and migrate:

   ```bash
   pnpm install --frozen-lockfile
   cd apps/api && uv sync --frozen && uv run alembic upgrade head && uv run python -m oriade.cli seed
   cd ../..
   pnpm dev
   ```

The web app runs at `http://localhost:3000`; the API runs at `http://localhost:8000` when started with `make api`.

Important environment variables are `DATABASE_URL`, `REDIS_URL`, `APP_ORIGIN`, `API_INTERNAL_URL`, `ENVIRONMENT`, `WHATSAPP_NUMBER`, and `SESSION_DAYS`. Never commit `.env` or credentials.

## Checks

```bash
pnpm test
pnpm typecheck
pnpm lint
pnpm build
cd apps/api && uv run pytest -q
```

For the end-to-end walkthrough, see [docs/DEMO.md](docs/DEMO.md). Deployment notes are in [docs/deployment/DEPLOYMENT.md](docs/deployment/DEPLOYMENT.md).

## WhatsApp ordering

The API persists an order in `PENDING_CONFIRMATION`, builds a URL-encoded message from validated database snapshots, and returns a `wa.me` link. The customer must press Send in WhatsApp; restaurant staff then explicitly confirm the order in Operations.

## Delivery

The repository is ready for container deployment with `docker-compose.yml` and the API/web Dockerfiles. No hosted deployment URL is claimed by this repository.
