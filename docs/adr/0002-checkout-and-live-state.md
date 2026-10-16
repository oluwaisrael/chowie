# ADR 0002 — Durable checkout, snapshot SSE

Status: accepted for the initial implementation.

Persist only non-sensitive cart selections in the browser. Create a durable order at checkout, validating current catalog prices and stock. Do not create server carts or DRAFT orders merely to fill a target schema. Cross-device cart synchronization is deferred.

Use PostgreSQL transaction and advisory locks for stock and duplicate submissions. An idempotency key binds an immutable request fingerprint to an owner and guest access hash. Store historical order item names, selected modifiers and prices. Money is integer kobo.

Use three-second authorized snapshot SSE initially. It naturally recovers missed updates and works across API replicas. Outbox events remain available for asynchronous consumers. Switch SSE wake-ups to the shared event channel if measurements justify it; retain snapshot recovery.

Consequences: modest database polling overhead; the first UI shows up to 100 most recent authorized orders. No claim of unbounded historical pagination or high-concurrency load capacity. Unconfirmed stock reservations require staff cancellation; automatic reservation expiry is future work.
