"""Email sending service — supports Gmail SMTP (App Password) and Gmail API."""

from __future__ import annotations

import logging
import smtplib
import socket
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """
    Email service that sends via Gmail SMTP (App Password).

    Setup (one-time):
    1. Enable 2-Step Verification on your Google Account
    2. Go to myaccount.google.com → Security → App passwords
    3. Generate an App Password for "Mail" → "Other (custom name)" → "AP Ops"
    4. Copy the 16-character password into .env as GMAIL_APP_PASSWORD
    5. Set GMAIL_SENDER_EMAIL to your Gmail address
    """

    @classmethod
    def send_email(
        cls,
        to: str,
        subject: str,
        body: str,
        html: bool = False,
        cc: Optional[str] = None,
        bcc: Optional[str] = None,
    ) -> dict:
        """
        Send an email via Gmail SMTP using an App Password.

        Returns:
            dict with 'success' bool and 'message_id' or 'error'.
        """
        sender_email = settings.GMAIL_SENDER_EMAIL
        app_password = settings.GMAIL_APP_PASSWORD

        # ── Validate config ──────────────────────────────────────────────
        if not sender_email:
            return {"success": False, "error": "GMAIL_SENDER_EMAIL not configured in .env"}
        if not app_password:
            return {
                "success": False,
                "error": (
                    "GMAIL_APP_PASSWORD not configured. "
                    "Go to myaccount.google.com → Security → App passwords to generate one."
                ),
            }

        try:
            # ── Build message ────────────────────────────────────────────
            msg = MIMEMultipart("alternative")
            msg["From"] = sender_email
            msg["To"] = to
            msg["Subject"] = subject
            if cc:
                msg["Cc"] = cc

            # Attach body (plain text or HTML)
            mime_type = "html" if html else "plain"
            msg.attach(MIMEText(body, mime_type))

            # Build recipient list
            recipients = [to]
            if cc:
                recipients += [addr.strip() for addr in cc.split(",")]
            if bcc:
                recipients += [addr.strip() for addr in bcc.split(",")]

            # ── Send via Gmail SMTP ──────────────────────────────────────
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context, timeout=30) as server:
                server.login(sender_email, app_password)
                server.sendmail(sender_email, recipients, msg.as_string())

            logger.info(f"Email sent successfully via SMTP to {to} (subject: {subject})")
            return {
                "success": True,
                "message_id": f"smtp-{hash(to + subject)}",
                "recipient": to,
            }

        except smtplib.SMTPAuthenticationError:
            error_msg = (
                "Gmail SMTP authentication failed. "
                "Make sure GMAIL_APP_PASSWORD is correct and 2-Step Verification is enabled."
            )
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

        except smtplib.SMTPException as e:
            logger.error(f"SMTP error sending email: {e}")
            return {"success": False, "error": f"SMTP error: {str(e)}"}

        except socket.timeout:
            logger.error(f"SMTP connection timed out sending email to {to}")
            return {"success": False, "error": "Email server connection timed out. Please try again."}

        except Exception as e:
            logger.error(f"Unexpected error sending email: {e}")
            return {"success": False, "error": str(e)}

    @classmethod
    def get_default_supplier_email(cls) -> str:
        """Get default supplier email recipient."""
        return settings.DEFAULT_SUPPLIER_EMAIL

    @classmethod
    def get_default_po_request_email(cls) -> str:
        """Get default PO request email recipient."""
        return settings.DEFAULT_PO_REQUEST_EMAIL

    @classmethod
    def get_approval_notification_emails(cls) -> list[str]:
        """Get comma-separated approval notification emails as list."""
        if not settings.APPROVAL_NOTIFICATION_EMAILS:
            return []
        return [e.strip() for e in settings.APPROVAL_NOTIFICATION_EMAILS.split(",")]
