# Óriade demo

This is the shortest complete customer-to-kitchen walkthrough.

1. Start PostgreSQL and Redis, apply migrations, seed the catalog, and start the API and storefront.
2. Open the storefront and choose a featured meal. Select an optional add-on, increase the quantity, and add it to the bag.
3. Open checkout, enter a name and phone number, choose a delivery zone, and enter an address. Submit **Save order & review**.
4. Confirm the order reference and server-calculated total on the tracking page. Choose **Continue to WhatsApp**, then press Send in WhatsApp if demonstrating the handoff.
5. Sign in to Operations with a seeded staff account, find the `PENDING_CONFIRMATION` order, and choose **Confirm order**.
6. Open Kitchen in a separate session. Move the order through **Accept & start preparing** and **Mark ready**.
7. Return to the customer tracking page and show the live status timeline updating.

Seeded staff accounts use `admin@example.com`, `operator@example.com`, or `kitchen@example.com` with the password `test-password-long` in the test fixture. Use a separate local seed account/password for a presentation environment.

The key product point is that WhatsApp opening is only a handoff: it does not mark the order confirmed, and no payment is collected.
