# Delivery plan

## Repository audit

- Workspace `/Users/mac/derin-food` was empty and was not a repository.
- Cloned `https://github.com/oluwaisrael/chowie.git` directly into the workspace; remote repository had no commits.
- No existing source, assets, history, license, or repository instructions to preserve.
- Attachment contained only the engineering directive. No homepage reference image was available.
- Work branch: `feat/oriade-platform`. Git contributor identity was already configured; unchanged.

## Vertical slices

1. PostgreSQL model, migrations, backend domain rules, identity, and concurrency tests.
2. Responsive storefront, menu, cart, API checkout, and private order tracking.
3. Staff menu/settings controls, order workflow, kitchen queue, operational reporting.
4. Reliability, browser QA, container configuration, documentation, GitHub delivery.

## Implementation decisions

- One Next.js app isolates storefront, operations and kitchen features; API authorization remains authoritative.
- PostgreSQL is required for tests and runtime, including advisory locks. No SQLite substitute.
- Browser-persisted carts contain only non-sensitive item selections. Checkout is the durable server boundary.
- Database snapshot SSE every three seconds is the initial replica-safe live transport. A transactional outbox and Celery publisher provide a future event wake-up boundary.
- Sample catalog has explicitly marked sample pickup/delivery information. No seeded orders or fabricated analytics.
- External services without credentials (SMTP, S3, production hosting) remain explicit configuration requirements.

See QUALITY-REPORT.md for executed checks and open limitations.
