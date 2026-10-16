# Database schema

PostgreSQL is mandatory; tests use real PostgreSQL and the same Alembic migration as deployment. UUID primary keys and timezone-aware creation timestamps are standard. Monetary fields are BIGINT kobo.

| Table | Purpose and constraints |
| --- | --- |
| users | Unique normalized email, password hash, active flag, constrained role |
| sessions | User FK, unique token hash, CSRF secret, expiry |
| password_resets | User FK, unique token hash, expiry, one-time used flag |
| addresses | User-owned label, address and phone |
| locations | Branch name, pickup address and active flag |
| delivery_zones | Location FK, non-negative fee and availability |
| categories | Unique name and slug |
| menu_items | Category/location FKs, non-negative price, description, image, availability |
| modifiers | Meal FK, non-negative price and availability |
| inventory | One row per meal; null stock means unlimited, otherwise non-negative portions |
| orders | Unique reference/key, request/access hashes, customer snapshot, branch, fulfillment, status, version and checked totals |
| order_items | Order/meal FKs, positive quantity, unit price and immutable modifier JSON snapshot |
| order_status_history | Ordered status changes and optional staff actor |
| whatsapp_handoffs | One per order; initiation timestamp, no delivery assertion |
| outbox_events | Transactional event payload and publication marker |
| notifications | Unique event receipt for idempotent processing |
| audit_logs | Actor, action, target and bounded application-supplied details |

Order items preserve historical values even after a menu edit. Orders preserve pickup/delivery address and fee snapshots. Foreign keys prevent deleting referenced catalog/identity records; staff retire items through availability flags. Fulfillment is part of the order aggregate, not a redundant parallel state table. Roles and permissions are static code policy. Carts are deliberately browser-local (ADR 0002).

Indexes cover email/token/key uniqueness, order status and owner/branch lookup, meal category/branch lookup, order item/history lookup, and outbox publication. The initial migration is explicit Alembic DDL; no runtime `create_all` is used.

## Commands

From `apps/api`:

```sh
uv run alembic upgrade head
uv run alembic check
uv run alembic revision --autogenerate -m 'describe schema change'
```

Review generated DDL before applying it. Use a backup and a forward migration for production rollbacks; do not blindly downgrade live business data.
