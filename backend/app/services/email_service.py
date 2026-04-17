from __future__ import annotations

import smtplib
from email.message import EmailMessage

from app.core.config import settings


def send_otp_email(email: str, code: str, expiry_minutes: int) -> bool:
    if not settings.smtp_configured:
        return False

    message = EmailMessage()
    message["Subject"] = "Your Plantation Yield Automation verification code"
    message["From"] = settings.smtp_from_email
    message["To"] = email
    message.set_content(
        (
            "Your verification code is "
            f"{code}. It will expire in {expiry_minutes} minute(s)."
        )
    )

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as server:
        server.ehlo()
        try:
            server.starttls()
            server.ehlo()
        except smtplib.SMTPException:
            pass

        if settings.smtp_user.strip():
            server.login(settings.smtp_user, settings.smtp_password)

        server.send_message(message)

    return True
