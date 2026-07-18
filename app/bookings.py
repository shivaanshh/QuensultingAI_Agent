"""Booking persistence: the database is now the source of truth (replaces
the old Google-Sheets-as-source-of-truth pattern). Sheets/email/webhook
remain best-effort notifications layered on top in app/main.py.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from .db_models import Booking, Tenant

logger = logging.getLogger("agent.bookings")

# Tool args that map to fixed Booking columns rather than the free-form
# extra_fields JSON blob. Category templates (Phase C) may send additional
# args beyond these (e.g. party_size, urgency_level) -- those fall through
# to extra_fields automatically, no backend change needed per category.
FIXED_BOOKING_ARGS = {
    "patient_name", "phone_number", "patient_email", "service",
    "preferred_datetime", "notes",
}


def compute_extra_fields(args: dict) -> dict:
    """Any tool arg that isn't a fixed column becomes a category-specific extra field."""
    return {
        k: v for k, v in args.items()
        if k not in FIXED_BOOKING_ARGS and v not in (None, "")
    }


def save_booking(
    db: Session,
    tenant: Tenant,
    *,
    booking_reference: str,
    service_name: str,
    customer_name: str,
    phone_number: str,
    email: str,
    preferred_datetime_raw: str,
    confirmed_datetime: str,
    notes: str,
    call_id: str,
    extra_fields: dict,
) -> Optional[Booking]:
    """Persist a booking. Returns the Booking row, or None if the write failed."""
    try:
        booking = Booking(
            tenant_id=tenant.id,
            booking_reference=booking_reference,
            service_name_snapshot=service_name,
            customer_name=customer_name,
            phone_number=phone_number,
            email=email,
            preferred_datetime_raw=preferred_datetime_raw,
            confirmed_datetime=confirmed_datetime,
            notes=notes,
            extra_fields=extra_fields,
            call_id=call_id,
            status="confirmed",
            created_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        )
        db.add(booking)
        db.commit()
        db.refresh(booking)
        logger.info("Booking %s saved for tenant %s", booking_reference, tenant.slug)
        return booking
    except Exception as exc:  # noqa: BLE001 - never let a write error crash the call
        db.rollback()
        logger.error("Failed to save booking for tenant %s: %s", tenant.slug, exc)
        return None
