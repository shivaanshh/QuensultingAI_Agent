"""Google Sheets persistence for booking records -- an OPTIONAL per-tenant
export, not the source of truth (the database is). A tenant with no
`google_sheets_id` set simply skips this; append_booking() returns False.

Uses a shared Google Cloud service account (gspread) across all tenants; the
service-account email must be given edit access to each tenant's sheet.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Optional

import gspread
from google.oauth2.service_account import Credentials

from .config import settings
from .db_models import Tenant

logger = logging.getLogger("agent.sheets")

_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

_HEADER = [
    "Timestamp",
    "Booking Reference",
    "Customer Name",
    "Phone",
    "Email",
    "Service",
    "Preferred Time",
    "Confirmed Time",
    "Notes",
    "Call ID",
    "Status",
]

_client: Optional[gspread.Client] = None


def _load_credentials() -> Credentials:
    """Load the shared service-account key from the JSON env var, or a file on disk."""
    if settings.GOOGLE_CREDENTIALS_JSON:
        info = json.loads(settings.GOOGLE_CREDENTIALS_JSON)
        return Credentials.from_service_account_info(info, scopes=_SCOPES)
    if os.path.exists(settings.GOOGLE_CREDENTIALS_FILE):
        return Credentials.from_service_account_file(
            settings.GOOGLE_CREDENTIALS_FILE, scopes=_SCOPES
        )
    raise RuntimeError(
        "No Google credentials configured. Set GOOGLE_CREDENTIALS_JSON (raw key) "
        f"or provide the key file at {settings.GOOGLE_CREDENTIALS_FILE}."
    )


def _get_worksheet(tenant: Tenant):
    """Return the tenant's Bookings worksheet, creating the header row if needed."""
    global _client
    if _client is None:
        _client = gspread.authorize(_load_credentials())

    spreadsheet = _client.open_by_key(tenant.google_sheets_id)
    try:
        ws = spreadsheet.worksheet(settings.BOOKINGS_WORKSHEET)
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(
            title=settings.BOOKINGS_WORKSHEET, rows=1000, cols=len(_HEADER)
        )
        ws.append_row(_HEADER, value_input_option="RAW")

    # Ensure header exists (first-run on an empty sheet).
    if not ws.acell("A1").value:
        ws.update("A1", [_HEADER])
    return ws


def append_booking(record: dict, tenant: Tenant) -> bool:
    """Append a single booking record to the tenant's optional Sheet.

    Returns True on success, False if Sheets isn't configured for this
    tenant or the write failed. Uses RAW input (not USER_ENTERED) so Sheets
    never auto-converts a phone number into a number and silently drops a
    leading zero.
    """
    if not tenant.google_sheets_id:
        return False

    row = [
        record.get("timestamp", ""),
        record.get("booking_reference", ""),
        record.get("customer_name", ""),
        record.get("phone_number", ""),
        record.get("email", ""),
        record.get("service", ""),
        record.get("preferred_datetime", ""),
        record.get("confirmed_datetime", ""),
        record.get("notes", ""),
        record.get("call_id", ""),
        record.get("status", ""),
    ]
    try:
        ws = _get_worksheet(tenant)
        ws.append_row(row, value_input_option="RAW")
        logger.info("Booking %s written to Google Sheets for tenant %s", record.get("booking_reference"), tenant.slug)
        return True
    except Exception as exc:  # noqa: BLE001 - never let logging break the call
        logger.error("Failed to write booking to Google Sheets for tenant %s: %s", tenant.slug, exc)
        return False
