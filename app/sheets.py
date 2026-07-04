"""Google Sheets persistence for caller / booking records.

Uses a Google Cloud service account (gspread). The service-account email must be
given edit access to the target sheet. If Sheets isn't configured, functions log
a warning and return False so the call flow can degrade gracefully rather than
crash.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Optional

import gspread
from google.oauth2.service_account import Credentials

from .config import settings

logger = logging.getLogger("dental.sheets")

_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

_HEADER = [
    "Timestamp",
    "Booking Reference",
    "Patient Name",
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
    """Load the service-account key from the JSON env var, or a file on disk."""
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


def _get_worksheet():
    """Return the Bookings worksheet, creating the header row if needed."""
    global _client
    if not settings.GOOGLE_SHEETS_ID:
        raise RuntimeError("GOOGLE_SHEETS_ID is not set")

    if _client is None:
        _client = gspread.authorize(_load_credentials())

    spreadsheet = _client.open_by_key(settings.GOOGLE_SHEETS_ID)
    try:
        ws = spreadsheet.worksheet(settings.BOOKINGS_WORKSHEET)
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(
            title=settings.BOOKINGS_WORKSHEET, rows=1000, cols=len(_HEADER)
        )
        ws.append_row(_HEADER, value_input_option="USER_ENTERED")

    # Ensure header exists (first-run on an empty sheet).
    if not ws.acell("A1").value:
        ws.update("A1", [_HEADER])
    return ws


def append_booking(record: dict) -> bool:
    """Append a single booking record. Returns True on success."""
    row = [
        record.get("timestamp", ""),
        record.get("booking_reference", ""),
        record.get("patient_name", ""),
        record.get("phone_number", ""),
        record.get("patient_email", ""),
        record.get("service", ""),
        record.get("preferred_datetime", ""),
        record.get("confirmed_datetime", ""),
        record.get("notes", ""),
        record.get("call_id", ""),
        record.get("status", ""),
    ]
    try:
        ws = _get_worksheet()
        ws.append_row(row, value_input_option="USER_ENTERED")
        logger.info("Booking %s written to Google Sheets", record.get("booking_reference"))
        return True
    except Exception as exc:  # noqa: BLE001 - never let logging break the call
        logger.error("Failed to write booking to Google Sheets: %s", exc)
        return False
