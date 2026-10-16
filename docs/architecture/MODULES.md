# Module ownership

| Module | Responsibility | Public application interface |
| --- | --- | --- |
| Identity | Argon2id credentials, hashed sessions, password reset | register, login, authenticate, request_reset, reset_password, logout |
| Customers | Account-owned saved addresses | addresses, save_address, delete_address |
| Catalog | Meal/category data and modifiers; image storage | catalog, save_item, upload |
| Commerce | Authoritative pricing and locked stock reservation | price_lines |
| Ordering | Idempotency, snapshots, transitions, order visibility | create_order, authorized_order, snapshot, list_orders, transition |
| Fulfillment | Branch and delivery-zone validation | validate_fulfillment |
| Operations | Privileged configuration, staff access, stock updates | save_entity, update_staff, update_stock |
| Notifications | WhatsApp formatting and SMTP delivery | whatsapp_url, send_reset, MessagingProvider protocol |
| Reporting | Aggregate operational read models | reports |
| Audit | Append-only privileged-action records | record |
| Workers | Outbox publication and deduplicated receipts | publish_outbox |

The API is presentation and dependency wiring; services own use cases. Pure rules in `ordering/domain.py` import no framework or infrastructure. Persistence mappings are centralized in `shared/models.py` to keep a single migration registry. This pragmatic version does not wrap every SQLAlchemy operation in a repository interface. Ordering calls commerce, fulfillment, identity hashing, notifications and audit through explicit service functions. Reporting reads across modules deliberately as a read model.

Inventory currently belongs to commerce reservation and operations stock management, rather than an empty standalone package. Customers use the user identity row rather than duplicating customer profile fields in a second table. Roles are a fixed, constrained enum with endpoint permission checks, not an editable permission graph. These boundaries can be extracted once actual complexity justifies them.
