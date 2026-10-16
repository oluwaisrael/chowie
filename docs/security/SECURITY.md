# Security model

## Identity and authorization

Passwords use Argon2id. Session cookies are HTTP-only, SameSite=Lax, and Secure in `ENVIRONMENT=production`. Session secrets are random 256-bit values stored only as SHA-256 hashes. Logout, password reset and staff access changes invalidate server-side sessions. Mutating cookie-authenticated requests need the session's CSRF header. All mutations require an exact configured Origin, including guest checkout and login. There is no permissive CORS policy; browsers use the same-origin Next.js API proxy.

Role policy: customers read their own orders and addresses; operators manage orders, catalog and delivery zones; kitchen accounts receive preparation details and can move confirmed → preparing → ready; administrators also manage locations, staff access and audit records. Kitchen order serialization omits names, addresses, phone numbers, totals and WhatsApp URLs. Free-text preparation instructions are retained, so staff should avoid copying unnecessary PII into that field.

Guest order secrets are held only in sessionStorage and sent in a header. References alone do not grant access. Customer data is never put in public page metadata. WhatsApp URLs intentionally contain the customer-approved order details; users must understand that opening the URL shares these with WhatsApp. No provider delivery claim is made.

## Abuse and input controls

Pydantic rejects unknown checkout fields and constrains quantities, lengths, IDs, roles and statuses. Database constraints reinforce money and stock rules. SQLAlchemy parameterizes queries. Redis provides atomic per-peer request limits for authentication, checkout and reset endpoints, and fails closed if unavailable. Under the current Next.js rewrite topology, API connections share the proxy address, so these are conservative aggregate limits. Configure edge per-client limits and explicitly trusted proxy identity before public scale; never trust arbitrary forwarded headers.

Image uploads are restricted to staff, capped at 5 MB after multipart parsing, pixel-limited and re-encoded to WebP before storage. Apply an ingress request-body limit as well, because multipart parsing precedes application validation. Object storage credentials and SMTP settings must be supplied as secrets.

Privileged mutations write audit rows. The application exposes no audit-edit endpoint, but database administrators can alter records; this is not a tamper-proof external audit service.

## Browser and deployment controls

Security headers include no-sniff, no-referrer, denied framing, restricted permissions and CSP. The current CSP allows Next.js inline scripts and inline styles; development alone permits eval. A nonce-based CSP and security penetration review remain hardening tasks. No authentication token is stored in localStorage; that storage holds only cart selections.

TLS termination, managed database encryption, network isolation, backup/restore drills, secret rotation, dependency review and retention/legal approval are deployment responsibilities. Production has no default administrator account. The explicit create-admin CLI prompts for a password. Test accounts are guarded by an `_e2e` database-name check and are never seeded by application startup.

## Known limits

No email verification, MFA, account recovery escalation, automatic reservation expiry, or branch-scoped staff permissions yet. Password reset needs working SMTP and its delivery has not been verified with a live provider. S3 upload logic has not been tested against a live bucket. See the quality report rather than assuming these integrations are production-certified.
