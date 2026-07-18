"""Endpoint tests for the FastAPI webhooks.

Runs against the in-memory test DB seeded in conftest.py (tenant slug
"quensulting-dental"). Google Sheets and notifications are stubbed so the
suite runs with no external services or credentials. Tenant webhook_secret
defaults to "" for the seeded tenant, so the token guard is disabled here
(it's exercised by test_token_required).
"""
import datetime as dt
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient

from app import db_models, main, utils
from tests.conftest import TENANT_SLUG

client = TestClient(main.app)

IST = ZoneInfo("Asia/Kolkata")
FIXED_NOW = dt.datetime(2026, 7, 4, 12, 0, tzinfo=IST)  # Saturday noon

BASE = f"/webhook/{TENANT_SLUG}"


@pytest.fixture(autouse=True)
def _freeze_now(monkeypatch):
    monkeypatch.setattr(utils, "now_clinic", lambda *a, **k: FIXED_NOW)


@pytest.fixture
def sheets_ok(monkeypatch):
    """Pretend Sheets + notifications all succeed."""
    monkeypatch.setattr(main, "append_booking", lambda record, tenant: True)
    monkeypatch.setattr(main, "send_confirmation_email", lambda record, tenant: True)
    monkeypatch.setattr(main, "fire_booking_webhook", lambda record, tenant: True)


# --- health -------------------------------------------------------------------
def test_health_ok():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# --- unknown tenant -------------------------------------------------------------
def test_unknown_tenant_404():
    r = client.post(
        "/webhook/not-a-real-tenant/check-availability",
        json={"args": {"preferred_datetime": "next Monday at 3pm", "service": "Dental Cleaning"}},
    )
    assert r.status_code == 404


# --- check-availability -------------------------------------------------------
def test_availability_in_hours():
    r = client.post(
        f"{BASE}/check-availability",
        json={"args": {"preferred_datetime": "next Monday at 3pm",
                       "service": "Dental Cleaning"}},
    )
    assert r.status_code == 200
    assert r.json()["available"] == "true"


def test_availability_sunday_closed_with_suggestions():
    r = client.post(
        f"{BASE}/check-availability",
        json={"args": {"preferred_datetime": "tomorrow at 11am",  # Sunday
                       "service": "Dental Cleaning"}},
    )
    body = r.json()
    assert body["available"] == "false"
    assert body["suggested_slots"]  # non-empty alternatives offered


def test_availability_unparseable():
    r = client.post(
        f"{BASE}/check-availability",
        json={"args": {"preferred_datetime": "", "service": "Dental Cleaning"}},
    )
    assert r.json()["available"] == "false"


# --- book-appointment ---------------------------------------------------------
def test_book_success(sheets_ok):
    r = client.post(
        f"{BASE}/book-appointment",
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
        f"{BASE}/book-appointment",
        json={"args": {"patient_name": "Priya Sharma"}},  # no phone/service/time
    )
    body = r.json()
    assert body["status"] == "failed"
    assert "phone_number" in body["message"]


def test_book_empty_strings_rejected():
    # Empty strings must not pass as "provided".
    r = client.post(
        f"{BASE}/book-appointment",
        json={"args": {"patient_name": "  ", "phone_number": "",
                       "service": "Dental Cleaning",
                       "preferred_datetime": "Monday 3pm"}},
    )
    assert r.json()["status"] == "failed"


def test_book_fails_when_db_save_fails(monkeypatch, sheets_ok):
    # The database is now the source of truth: if it fails, the booking fails.
    monkeypatch.setattr(main, "save_booking", lambda *a, **k: None)
    r = client.post(
        f"{BASE}/book-appointment",
        json={"args": {"patient_name": "Priya Sharma",
                       "phone_number": "9812345678",
                       "service": "Dental Cleaning",
                       "preferred_datetime": "next Monday at 3pm"}},
    )
    assert r.json()["status"] == "failed"


def test_book_persists_extra_fields(sheets_ok, db_session):
    # Args beyond the fixed booking columns (category-specific slots) should
    # land in extra_fields without any backend change.
    r = client.post(
        f"{BASE}/book-appointment",
        json={"args": {"patient_name": "Priya Sharma",
                       "phone_number": "9812345678",
                       "service": "Dental Cleaning",
                       "preferred_datetime": "next Monday at 3pm",
                       "insurance_provider": "Star Health"}},
    )
    reference = r.json()["booking_reference"]
    booking = (
        db_session.query(db_models.Booking)
        .filter_by(booking_reference=reference)
        .first()
    )
    assert booking is not None
    assert booking.extra_fields.get("insurance_provider") == "Star Health"


def test_notifications_never_block_booking(monkeypatch):
    # Email/webhook raising must NOT fail a booking already saved to the DB.
    monkeypatch.setattr(main, "append_booking", lambda record, tenant: True)

    def _boom(record, tenant):
        raise RuntimeError("smtp down")

    monkeypatch.setattr(main, "send_confirmation_email", _boom)
    monkeypatch.setattr(main, "fire_booking_webhook", _boom)
    r = client.post(
        f"{BASE}/book-appointment",
        json={"args": {"patient_name": "Priya Sharma",
                       "phone_number": "9812345678",
                       "service": "Dental Cleaning",
                       "preferred_datetime": "next Monday at 3pm"}},
    )
    # Booking still succeeds because the record is already persisted.
    assert r.json()["status"] == "success"


# --- token guard --------------------------------------------------------------
def test_token_required(db_session):
    tenant = db_session.query(db_models.Tenant).filter_by(slug=TENANT_SLUG).first()
    tenant.webhook_secret = "s3cret"
    db_session.commit()
    try:
        # No token -> rejected.
        r = client.post(
            f"{BASE}/check-availability",
            json={"args": {"preferred_datetime": "Monday 3pm", "service": "Dental Cleaning"}},
        )
        assert r.status_code == 401
        # Correct token -> allowed.
        r = client.post(
            f"{BASE}/check-availability?token=s3cret",
            json={"args": {"preferred_datetime": "next Monday at 3pm", "service": "Dental Cleaning"}},
        )
        assert r.status_code == 200
    finally:
        tenant.webhook_secret = ""
        db_session.commit()
