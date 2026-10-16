# Architecture

Óriade is a domain-oriented modular monolith with one Next.js application and one FastAPI application. PostgreSQL is authoritative. Redis supports rate limits and the Celery broker; no order depends on Redis for durable storage.

## Runtime

The browser uses the same-origin `/api` proxy in Next.js. FastAPI validates the origin, session, CSRF token, input schema and permissions. Application services coordinate transactions and module calls. SQLAlchemy mappings and integrations live outside pure business rules. The pure ordering domain defines money calculations and the fulfillment-aware state machine.

Storefront, operations and kitchen are separate feature modules and route areas within one deployment. Their shared shell, tokens, API client and session handling avoid three competing application foundations. Backend role checks enforce access even if a caller bypasses the UI.

## Checkout transaction

1. Validate customer details, selected branch, fulfillment zone and item IDs.
2. Acquire a PostgreSQL advisory transaction lock derived from the idempotency key.
3. Return an existing order only when request fingerprint, guest access hash and authenticated owner match.
4. Lock meals, modifiers and inventory in a consistent order; reserve available portions.
5. Recalculate integer-kobo totals from database prices.
6. Insert order, immutable item snapshots, initial status, handoff record and outbox event atomically.
7. Return the validated summary and encoded WhatsApp link.

The guest access secret is generated with Web Crypto and held in sessionStorage; only its SHA-256 hash is persisted. Order URLs contain a reference, never an access token. An account owner can also access their own order. Session cookies are HTTP-only.

WhatsApp handoff initiation is an independently recorded action. It never confirms an order or asserts message delivery. Operators confirm through the authenticated API.

## Live operations

SSE returns an authorized snapshot when it changes, with a heartbeat otherwise. Connections reconnect after closure and recover complete state from PostgreSQL; authorization is rechecked every three seconds. No process-local event bus is required, so replicas see the same orders. Lists use batched queries rather than per-order item/history queries.

The outbox publisher uses `FOR UPDATE SKIP LOCKED`, bounded Celery retries, Redis notification hints, and an idempotent notification receipt table. Its delivery is at least once. SSE currently polls PostgreSQL rather than consuming the Redis hints, providing correctness without dependence on event delivery. This is an initial-scale tradeoff, not a claim of unlimited throughput.

## External boundaries

- S3-compatible storage: image decoding, metadata stripping through WebP re-encoding, dimension and payload limits, unique immutable keys.
- SMTP: expiring password reset links; unavailable configuration is reported honestly.
- Sentry: opt-in SDK initialization with default PII collection disabled.
- OpenTelemetry: FastAPI instrumentation hook; collector/exporter wiring remains a deployment task.
- WhatsApp Cloud API: protocol boundary only, no live provider or automatic messages.

See [module ownership](MODULES.md), [diagrams](DIAGRAMS.md), [schema](../database/SCHEMA.md), and [decisions](../adr/0001-modular-monolith.md).
