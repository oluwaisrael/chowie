import smtplib
import ssl
from email.message import EmailMessage
from oriade.shared.config import settings
from oriade.shared.errors import Problem


def send_reset(email, token):
    config = settings()
    if not config.smtp_host:
        raise Problem("Password reset email is not configured. Please contact the restaurant.", 503)
    message = EmailMessage()
    message["Subject"] = "Reset your Óriade password"
    message["From"], message["To"] = config.smtp_from, email
    message.set_content(
        f"Reset your password within 30 minutes:\n{config.app_origin}/reset-password#token={token}\n\nIf you did not request this, you can ignore this email."
    )
    with smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=15) as server:
        server.starttls(context=ssl.create_default_context())
        if config.smtp_username:
            server.login(config.smtp_username, config.smtp_password)
        server.send_message(message)
