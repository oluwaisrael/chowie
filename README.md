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

## How to run locally

Prerequisites: Node.js 20+, pnpm, Python 3.12+, `uv`, Docker Desktop, and a running Docker daemon.

1. Copy `.env.example` to `.env` and adjust values only if your local services use different ports.
2. Start PostgreSQL and Redis, or use the supplied Compose file:

   ```bash
   docker compose up -d db redis
   ```

3. Install dependencies and prepare the API database:

   ```bash
   pnpm install --frozen-lockfile
   cd apps/api
   uv sync --frozen
   uv run alembic upgrade head
   uv run python -m oriade.cli seed
   cd ../..
   ```

4. Start the API in Terminal 1:

   ```bash
   make api
   ```

5. Start the storefront in Terminal 2:

   ```bash
   pnpm dev
   ```

6. Inspect the application at `http://localhost:3000`. The API is available at `http://localhost:8000/health`.

To run the full stack with containers instead, use:

```bash
docker compose up --build
```

Then open `http://localhost:3000`.

The sample seed now adds Nigerian and international menu examples and all 20 Lagos LGAs. It can be rerun safely to add missing demo dishes/areas; the sample delivery fees and prices are illustrative and must be reviewed in Operations → Menu and Settings before taking real orders. For an already-running local database, rerun the seed from `apps/api` after migrations.

For Paystack, create an account and find test credentials in the Paystack Dashboard under Settings → API Keys & Webhooks. Put the **test secret key** (`sk_test_…`) in the root `.env` as `PAYSTACK_SECRET_KEY`; never put a secret key in browser code or commit it. Use live keys only after your Paystack account is approved and the business is ready to accept real payments. Configure the Paystack webhook URL as `/payments/paystack/webhook` on the API host. See [Paystack authentication](https://paystack.com/docs/api/authentication/) and [transaction API](https://paystack.com/docs/api/transaction/).

Order status updates and payment confirmations can be sent using [Resend](https://resend.com/): create an API key in its dashboard and set `RESEND_API_KEY` and `ORDER_EMAIL_FROM` in `.env`. For production, verify a domain in Resend and use a sender on that domain. Without those values, orders still work; automatic emails are skipped and staff's “Resend order email” action explains that email is not configured. Customer order tracking also offers a WhatsApp handoff and pay-on-delivery orders do not start a Paystack charge.

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

The seeded Lagos delivery areas are Agege, Ajeromi-Ifelodun, Alimosho, Amuwo-Odofin, Apapa, Badagry, Epe, Eti-Osa, Ibeju-Lekki, Ifako-Ijaiye, Ikeja, Ikorodu, Kosofe, Lagos Island, Lagos Mainland, Mushin, Ojo, Oshodi-Isolo, Shomolu and Surulere. Coverage and delivery fees are sample settings, not a promise that delivery is available throughout each LGA. Adjust or deactivate zones in Operations → Settings.
