"""Post-booking notifications: a confirmation email (SMTP) and an optional
outbound webhook. Both are best-effort — a failure here never fails the booking,
because the source-of-truth record is already in Google Sheets.
"""
from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import httpx

from .config import settings

logger = logging.getLogger("dental.notify")


def _build_email_html(record: dict) -> str:
    return f"""\
<div style="font-family:Arial,sans-serif;max-width:520px;margin:auto;color:#1f2937">
  <h2 style="color:#0d9488;margin-bottom:4px">Appointment Confirmed</h2>
  <p style="color:#6b7280;margin-top:0">{settings.CLINIC_NAME}</p>
  <p>Hi {record.get('patient_name', 'there')}, your appointment is booked. Here are the details:</p>
  <table style="border-collapse:collapse;width:100%">
    <tr><td style="padding:6px 0;color:#6b7280">Booking reference</td>
        <td style="padding:6px 0;font-weight:bold">{record.get('booking_reference','')}</td></tr>
    <tr><td style="padding:6px 0;color:#6b7280">Service</td>
        <td style="padding:6px 0">{record.get('service','')}</td></tr>
    <tr><td style="padding:6px 0;color:#6b7280">Date &amp; time</td>
        <td style="padding:6px 0">{record.get('confirmed_datetime','')}</td></tr>
    <tr><td style="padding:6px 0;color:#6b7280">Phone on file</td>
        <td style="padding:6px 0">{record.get('phone_number','')}</td></tr>
  </table>
  <p style="margin-top:16px">We're at 3rd Floor, Baner Business Hub, Baner Road, Pune 411045.
     Open Mon-Sat, 9 AM - 6 PM. Need to change something? Just call us back.</p>
  <p style="color:#9ca3af;font-size:12px">This is an automated confirmation from the {settings.CLINIC_NAME} reception line.</p>
</div>"""


def send_confirmation_email(record: dict) -> bool:
    """Send the confirmation email to the patient (and CC the clinic inbox)."""
    to_email = record.get("patient_email", "").strip()
    if not to_email:
        logger.info("No patient email provided; skipping confirmation email.")
        return False
    if not (settings.SMTP_USER and settings.SMTP_PASSWORD):
        logger.warning("SMTP not configured; skipping confirmation email.")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Appointment Confirmed — {settings.CLINIC_NAME} ({record.get('booking_reference','')})"
    msg["From"] = settings.FROM_EMAIL
    msg["To"] = to_email
    recipients = [to_email]
    if settings.CLINIC_INBOX:
        msg["Cc"] = settings.CLINIC_INBOX
        recipients.append(settings.CLINIC_INBOX)

    msg.attach(MIMEText(_build_email_html(record), "html"))

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.FROM_EMAIL, recipients, msg.as_string())
        logger.info("Confirmation email sent to %s", to_email)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to send confirmation email: %s", exc)
        return False


def fire_booking_webhook(record: dict) -> bool:
    """Optionally POST the booking to an external webhook (n8n / Zapier / CRM)."""
    if not settings.BOOKING_WEBHOOK_URL:
        return False
    try:
        resp = httpx.post(settings.BOOKING_WEBHOOK_URL, json=record, timeout=10)
        resp.raise_for_status()
        logger.info("Booking webhook fired -> %s", settings.BOOKING_WEBHOOK_URL)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to fire booking webhook: %s", exc)
        return False
