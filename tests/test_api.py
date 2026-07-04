"""Endpoint tests for the FastAPI webhooks.

Google Sheets and notifications are stubbed so the suite runs with no external
services or credentials. WEBHOOK_SECRET defaults to "" in tests, so the token
guard is disabled here (it's exercised by test_token_required).
"""
import datetime as dt
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient

from app import main, utils

client = TestClient(main.app)

IST = ZoneInfo("Asia/Kolkata")
FIXED_NOW = dt.datetime(2026, 7, 4, 12, 0, tzinfo=IST)  # Saturday noon


@pytest.fixture(autouse=True)
def _freeze_now(monkeypatch):
    monkeypatch.setattr(utils, "now_clinic", lambda: FIXED_NOW)


@pytest.fixture
def sheets_ok(monkeypatch):
    """Pretend Sheets + notifications all succeed."""
    monkeypatch.setattr(main, "append_booking", lambda record: True)
    monkeypatch.setattr(main, "send_confirmation_email", lambda record: True)
    monkeypatch.setattr(main, "fire_booking_webhook", lambda record: True)


# --- health -------------------------------------------------------------------
def test_health_ok():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# --- check-availability -------------------------------------------------------
def test_availability_in_hours():
    r = client.post(
        "/webhook/check-availability",
        json={"args": {"preferred_datetime": "next Monday at 3pm",
                       "service": "Dental Cleaning"}},
    )
    assert r.status_code == 200
    assert r.json()["available"] == "true"


def test_availability_sunday_closed_with_suggestions():
    r = client.post(
        "/webhook/check-availability",
        json={"args": {"preferred_datetime": "tomorrow at 11am",  # Sunday
                       "service": "Dental Cleaning"}},
    )
    body = r.json()
    assert body["available"] == "false"
    assert body["suggested_slots"]  # non-empty alternatives offered


def test_availability_unparseable():
    r = client.post(
        "/webhook/check-availability",
        json={"args": {"preferred_datetime": "", "service": "Dental Cleaning"}},
    )
    assert r.json()["available"] == "false"


# --- book-appointment ---------------------------------------------------------
def test_book_success(sheets_ok):
    r = client.post(
        "/webhook/book-appointment",
        json={"call": {"call_id": "abc"},
              "args": {"patient_name": "Priya Sharma",
                       "phone_number": "9812345678",
                       "patient_email": "priya@example.com",
                       "service": "Root Canal Treatment",
                       "preferred_datetime": "next Monday at 3pm"}},
    )
    body = r.json()
    assert body["status"] == "success"
    assert body["booking_reference"].startswith("QDC-")
    assert body["confirmed_datetime"]


def test_book_missing_fields():
    r = client.post(
        "/webhook/book-appointment",
        json={"args": {"patient_name": "Priya Sharma"}},  # no phone/service/time
    )
    body = r.json()
    assert body["status"] == "failed"
    assert "phone_number" in body["message"]


def test_book_empty_strings_rejected():
    # Empty strings must not pass as "provided".
    r = client.post(
        "/webhook/book-appointment",
        json={"args": {"patient_name": "  ", "phone_number": "",
                       "service": "Dental Cleaning",
                       "preferred_datetime": "Monday 3pm"}},
    )
    assert r.json()["status"] == "failed"


def test_book_fails_when_sheets_down(monkeypatch):
    # Sheets is the source of truth: if it fails, the booking fails.
    monkeypatch.setattr(main, "append_booking", lambda record: False)
    r = client.post(
        "/webhook/book-appointment",
        json={"args": {"patient_name": "Priya Sharma",
                       "phone_number": "9812345678",
                       "service": "Dental Cleaning",
                       "preferred_datetime": "next Monday at 3pm"}},
    )
    assert r.json()["status"] == "failed"


def test_notifications_never_block_booking(monkeypatch):
    # Email/webhook raising must NOT fail a booking already saved to Sheets.
    monkeypatch.setattr(main, "append_booking", lambda record: True)

    def _boom(record):
        raise RuntimeError("smtp down")

    monkeypatch.setattr(main, "send_confirmation_email", _boom)
    monkeypatch.setattr(main, "fire_booking_webhook", _boom)
    r = client.post(
        "/webhook/book-appointment",
        json={"args": {"patient_name": "Priya Sharma",
                       "phone_number": "9812345678",
                       "service": "Dental Cleaning",
                       "preferred_datetime": "next Monday at 3pm"}},
    )
    # Booking still succeeds because the record is already persisted.
    assert r.json()["status"] == "success"


# --- token guard --------------------------------------------------------------
def test_token_required(monkeypatch):
    monkeypatch.setattr(main.settings, "WEBHOOK_SECRET", "s3cret")
    # No token -> rejected.
    r = client.post(
        "/webhook/check-availability",
        json={"args": {"preferred_datetime": "Monday 3pm", "service": "Dental Cleaning"}},
    )
    assert r.status_code == 401
    # Correct token -> allowed.
    r = client.post(
        "/webhook/check-availability?token=s3cret",
        json={"args": {"preferred_datetime": "next Monday at 3pm", "service": "Dental Cleaning"}},
    )
    assert r.status_code == 200
