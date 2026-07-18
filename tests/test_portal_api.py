"""Tests for the business-owner portal API (app/portal_api.py): call log,
analytics, and CRUD for bookings / services / settings.

Reuses conftest's in-memory SQLite + dependency_overrides. Unique slugs per
test (uuid suffix) since the session-scoped DB is not rolled back between
tests -- same discipline as test_provisioning / test_admin_api.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app import db_models, main
from tests.conftest import TestSessionLocal

client = TestClient(main.app)


def _slug(prefix: str = "portal-test") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def _make_tenant(**overrides) -> db_models.Tenant:
    session = TestSessionLocal()
    try:
        tenant = db_models.Tenant(
            slug=overrides.pop("slug", _slug()),
            category=overrides.pop("category", "dental_medical"),
            business_name=overrides.pop("business_name", "Portal Test Clinic"),
            timezone="Asia/Kolkata",
            open_hour=9,
            close_hour=18,
            open_weekdays=[0, 1, 2, 3, 4, 5],
            webhook_secret="",
            booking_reference_prefix="PT",
            **overrides,
        )
        session.add(tenant)
        session.commit()
        session.refresh(tenant)
        return tenant
    finally:
        session.close()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _add_booking(tenant_id: int, **overrides) -> db_models.Booking:
    session = TestSessionLocal()
    try:
        booking = db_models.Booking(
            tenant_id=tenant_id,
            booking_reference=overrides.pop("booking_reference", _slug("REF")),
            service_name_snapshot=overrides.pop("service_name_snapshot", "Cleaning"),
            customer_name=overrides.pop("customer_name", "Alex Doe"),
            phone_number="+10000000000",
            preferred_datetime_raw="tomorrow 10am",
            confirmed_datetime="Tomorrow at 10:00 AM",
            created_at=overrides.pop("created_at", _now()),
            **overrides,
        )
        session.add(booking)
        session.commit()
        session.refresh(booking)
        return booking
    finally:
        session.close()


# --------------------------------------------------------------------------- #
# Call log + webhook persistence
# --------------------------------------------------------------------------- #
def test_calls_empty_for_new_tenant():
    tenant = _make_tenant()
    res = client.get(f"/api/tenants/{tenant.slug}/calls")
    assert res.status_code == 200
    assert res.json() == []


def test_calls_unknown_tenant_is_404():
    res = client.get("/api/tenants/nope-does-not-exist/calls")
    assert res.status_code == 404


def test_webhook_records_and_upserts_call():
    tenant = _make_tenant()
    call_id = _slug("call")

    # 1) call_started
    r1 = client.post(
        f"/webhook/{tenant.slug}/retell-events",
        json={"event": "call_started", "call": {"call_id": call_id, "from_number": "+199", "direction": "inbound"}},
    )
    assert r1.status_code == 200

    calls = client.get(f"/api/tenants/{tenant.slug}/calls").json()
    assert len(calls) == 1
    assert calls[0]["call_id"] == call_id
    assert calls[0]["call_status"] == "ongoing"

    # 2) call_analyzed for the SAME call -> upsert, not a new row
    r2 = client.post(
        f"/webhook/{tenant.slug}/retell-events",
        json={
            "event": "call_analyzed",
            "call": {
                "call_id": call_id,
                "duration_ms": 42000,
                "call_analysis": {"user_sentiment": "Positive", "call_successful": True, "call_summary": "Booked a cleaning."},
            },
        },
    )
    assert r2.status_code == 200

    calls = client.get(f"/api/tenants/{tenant.slug}/calls").json()
    assert len(calls) == 1
    row = calls[0]
    assert row["call_status"] == "analyzed"
    assert row["duration_seconds"] == 42
    assert row["user_sentiment"] == "Positive"
    assert row["call_successful"] is True
    assert "cleaning" in row["summary"].lower()


# --------------------------------------------------------------------------- #
# Analytics
# --------------------------------------------------------------------------- #
def test_analytics_structure_and_counts():
    tenant = _make_tenant()
    _add_booking(tenant.id, service_name_snapshot="Cleaning")
    _add_booking(tenant.id, service_name_snapshot="Cleaning")
    _add_booking(tenant.id, service_name_snapshot="Whitening")
    client.post(
        f"/webhook/{tenant.slug}/retell-events",
        json={"event": "call_ended", "call": {"call_id": _slug("c"), "duration_ms": 60000}},
    )

    res = client.get(f"/api/tenants/{tenant.slug}/analytics?days=30")
    assert res.status_code == 200
    data = res.json()
    assert data["days"] == 30
    assert data["total_bookings"] == 3
    assert data["total_calls"] == 1
    assert data["answered_calls"] == 1
    assert data["total_call_minutes"] == 1.0
    assert len(data["series"]) == 30
    labels = {s["label"]: s["count"] for s in data["top_services"]}
    assert labels.get("Cleaning") == 2
    assert labels.get("Whitening") == 1
    # conversion = bookings / calls
    assert data["booking_conversion"] == 3.0


def test_analytics_days_clamped():
    tenant = _make_tenant()
    assert client.get(f"/api/tenants/{tenant.slug}/analytics?days=1").json()["days"] == 7
    assert client.get(f"/api/tenants/{tenant.slug}/analytics?days=999").json()["days"] == 90


# --------------------------------------------------------------------------- #
# Bookings
# --------------------------------------------------------------------------- #
def test_update_booking_status():
    tenant = _make_tenant()
    booking = _add_booking(tenant.id)
    res = client.patch(f"/api/tenants/{tenant.slug}/bookings/{booking.id}", json={"status": "completed"})
    assert res.status_code == 200
    assert res.json()["status"] == "completed"


def test_update_booking_invalid_status_is_422():
    tenant = _make_tenant()
    booking = _add_booking(tenant.id)
    res = client.patch(f"/api/tenants/{tenant.slug}/bookings/{booking.id}", json={"status": "banana"})
    assert res.status_code == 422


def test_update_booking_unknown_is_404():
    tenant = _make_tenant()
    res = client.patch(f"/api/tenants/{tenant.slug}/bookings/999999", json={"status": "cancelled"})
    assert res.status_code == 404


# --------------------------------------------------------------------------- #
# Services CRUD
# --------------------------------------------------------------------------- #
def test_services_crud_roundtrip():
    tenant = _make_tenant()

    # create
    created = client.post(
        f"/api/tenants/{tenant.slug}/services",
        json={"name": "Root Canal", "price_display": "$300", "duration_minutes": 60},
    )
    assert created.status_code == 201
    sid = created.json()["id"]
    assert created.json()["is_active"] is True

    # list
    listed = client.get(f"/api/tenants/{tenant.slug}/services").json()
    assert any(s["id"] == sid for s in listed)

    # update / toggle inactive
    updated = client.patch(f"/api/tenants/{tenant.slug}/services/{sid}", json={"is_active": False, "price_display": "$350"})
    assert updated.status_code == 200
    assert updated.json()["is_active"] is False
    assert updated.json()["price_display"] == "$350"

    # delete
    assert client.delete(f"/api/tenants/{tenant.slug}/services/{sid}").status_code == 204
    listed_after = client.get(f"/api/tenants/{tenant.slug}/services").json()
    assert all(s["id"] != sid for s in listed_after)


def test_update_service_unknown_is_404():
    tenant = _make_tenant()
    res = client.patch(f"/api/tenants/{tenant.slug}/services/999999", json={"name": "X"})
    assert res.status_code == 404


# --------------------------------------------------------------------------- #
# Settings
# --------------------------------------------------------------------------- #
def test_update_settings_success():
    tenant = _make_tenant()
    res = client.patch(
        f"/api/tenants/{tenant.slug}/settings",
        json={"open_hour": 8, "close_hour": 20, "transfer_number": "+1888", "status": "paused"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["open_hour"] == 8
    assert body["close_hour"] == 20
    assert body["transfer_number"] == "+1888"
    assert body["status"] == "paused"
    assert "webhook_secret" not in body


def test_update_settings_bad_hours_is_422():
    tenant = _make_tenant()
    res = client.patch(f"/api/tenants/{tenant.slug}/settings", json={"open_hour": 18, "close_hour": 9})
    assert res.status_code == 422


def test_update_settings_bad_weekdays_is_422():
    tenant = _make_tenant()
    res = client.patch(f"/api/tenants/{tenant.slug}/settings", json={"open_weekdays": [0, 7]})
    assert res.status_code == 422
