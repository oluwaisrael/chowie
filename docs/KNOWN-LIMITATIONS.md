# Known limitations

- WhatsApp uses standard click-to-chat. Meta Cloud API delivery receipts and automated outbound messages are not connected.
- There is no payment gateway by design; payment is arranged with the restaurant after WhatsApp confirmation.
- Email password-reset delivery requires SMTP configuration. Without it, the API does not pretend an email was sent.
- Image uploads require configured S3-compatible storage; the seeded catalog uses local public images.
- The current deployment documentation describes container deployment, but this repository does not claim a hosted production URL.
- Order tracking uses authenticated ownership or a high-entropy guest access token; guest accounts are not full customer profiles.
