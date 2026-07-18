"""Post-booking notifications: a confirmation email (SMTP) and an optional
outbound webhook. Both are best-effort — a failure here never fails the
booking, because the source-of-truth record is already in the database.

Business facts (name, address, hours, CC inbox, webhook URL) come from the
tenant row; SMTP transport credentials are a shared platform-level setting
for every tenant in v1.
"""
from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

import httpx

from .config import settings
from .db_models import Tenant

logger = logging.getLogger("agent.notify")


def _build_email_html(record: dict, tenant: Tenant) -> str:
    close_pm = tenant.close_hour - 12 if tenant.close_hour > 12 else tenant.close_hour
    hours_sentence = f"Open {tenant.open_hour} AM - {close_pm} PM."
    location_sentence = f"We're at {tenant.address}. {hours_sentence}" if tenant.address else hours_sentence
    return f"""\
<div style="font-family:Arial,sans-serif;max-width:520px;margin:auto;color:#1f2937">
  <h2 style="color:#0d9488;margin-bottom:4px">Booking Confirmed</h2>
  <p style="color:#6b7280;margin-top:0">{tenant.business_name}</p>
  <p>Hi {record.get('customer_name', 'there')}, your booking is confirmed. Here are the details:</p>
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
  <p style="margin-top:16px">{location_sentence}
     Need to change something? Just call us back.</p>
  <p style="color:#9ca3af;font-size:12px">This is an automated confirmation from the {tenant.business_name} reception line.</p>
</div>"""


def _send_smtp(subject: str, html_body: str, to_addrs: list[str], cc_addrs: Optional[list[str]] = None) -> bool:
    """Shared SMTP connect/send boilerplate -- one shared sending identity
    (settings.SMTP_*) for every caller in v1. Best-effort: catches and logs
    everything, never raises."""
    if not (settings.SMTP_USER and settings.SMTP_PASSWORD):
        logger.warning("SMTP not configured; skipping email send.")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.FROM_EMAIL
    msg["To"] = ", ".join(to_addrs)
    recipients = list(to_addrs)
    if cc_addrs:
        msg["Cc"] = ", ".join(cc_addrs)
        recipients += cc_addrs

    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.FROM_EMAIL, recipients, msg.as_string())
        logger.info("Email sent to %s (subject=%r)", recipients, subject)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to send email (subject=%r): %s", subject, exc)
        return False


def send_confirmation_email(record: dict, tenant: Tenant) -> bool:
    """Send the confirmation email to the customer (and CC the tenant's inbox)."""
    to_email = record.get("email", "").strip()
    if not to_email:
        logger.info("No customer email provided; skipping confirmation email.")
        return False

    cc_addrs = [tenant.notification_email] if tenant.notification_email else None
    sent = _send_smtp(
        f"Booking Confirmed — {tenant.business_name} ({record.get('booking_reference','')})",
        _build_email_html(record, tenant),
        [to_email],
        cc_addrs,
    )
    if sent:
        logger.info("Confirmation email sent to %s for tenant %s", to_email, tenant.slug)
    return sent


def send_contact_notification(name: str, email: str, message: str, *, business_type: str = "") -> bool:
    """Best-effort notification for a marketing-site contact-form submission.

    Sent to the platform's own inbox (settings.FROM_EMAIL), not a tenant's --
    this is a prospective-customer inquiry, not a booking.
    """
    if not settings.FROM_EMAIL:
        logger.warning("FROM_EMAIL not configured; skipping contact notification.")
        return False
    body = f"""\
<div style="font-family:Arial,sans-serif;max-width:520px;margin:auto;color:#1f2937">
  <h2 style="color:#0d9488;margin-bottom:4px">New contact form submission</h2>
  <p><strong>Name:</strong> {name}</p>
  <p><strong>Email:</strong> {email}</p>
  <p><strong>Business type:</strong> {business_type or '(not specified)'}</p>
  <p><strong>Message:</strong></p>
  <p style="white-space:pre-wrap">{message}</p>
</div>"""
    return _send_smtp(f"New contact inquiry from {name}", body, [settings.FROM_EMAIL])


def fire_booking_webhook(record: dict, tenant: Tenant) -> bool:
    """Optionally POST the booking to the tenant's external webhook (n8n / Zapier / CRM)."""
    if not tenant.booking_webhook_url:
        return False
    try:
        resp = httpx.post(tenant.booking_webhook_url, json=record, timeout=10)
        resp.raise_for_status()
        logger.info("Booking webhook fired for tenant %s -> %s", tenant.slug, tenant.booking_webhook_url)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to fire booking webhook for tenant %s: %s", tenant.slug, exc)
        return False
