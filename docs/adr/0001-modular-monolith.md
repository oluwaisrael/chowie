# ADR 0001 — One web app, one modular API

Status: accepted for the initial implementation.

One restaurant does not justify three independently deployed Next.js applications or microservices. Keep storefront, operations and kitchen in distinct route/feature areas with one design system and API client. Keep the backend in domain-oriented modules with one PostgreSQL transaction boundary.

Consequences: simpler deployment and shared sessions; roles are enforced server-side. Independent frontend extraction remains possible through the existing feature boundaries. Staff access currently spans all branches; branch-scoped staff permissions are future work.
