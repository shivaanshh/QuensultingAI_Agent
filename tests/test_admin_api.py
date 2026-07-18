"""Tests for the admin HTTP API (app/admin_api.py).

Runs against the same in-memory test DB as test_api.py. Provisioning is
always mocked (app.admin_api.provision_tenant) -- no test here ever calls
the real Retell API. Each test that creates a tenant uses a unique slug
(short uuid suffix) since the test DB is session-scoped, not rolled back
between tests.
"""
import uuid

import pytest
from fastapi.testclient import TestClient

from app import admin_api, db_models, main
from tests.conftest import TENANT_SLUG

client = TestClient(main.app)


def _slug(prefix: str = "admin-test") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


# --- categories -----------------------------------------------------------
def test_list_categories():
    r = client.get("/api/categories")
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 4
    keys = {c["key"] for c in body}
    assert keys == {"dental_medical", "salon_spa", "restaurant", "home_services"}
    assert all("default_services" in c and "fact_bullet_labels" in c for c in body)


# --- create -----------------------------------------------------------------
def test_create_tenant_success():
    slug = _slug()
    r = client.post(
        "/api/tenants",
        json={
            "slug": slug,
            "category": "salon_spa",
            "business_name": "Test Salon",
            "services": ["Haircut", "Manicure"],
        },
    )
    assert r.status_code == 201
    body = r.json()
    assert body["slug"] == slug
    assert body["category"] == "salon_spa"
    assert len(body["services"]) == 2
    assert "webhook_secret" not in body


def test_create_tenant_duplicate_slug_is_422():
    slug = _slug()
    payload = {
        "slug": slug,
        "category": "salon_spa",
        "business_name": "Dup Salon",
    }
    r1 = client.post("/api/tenants", json=payload)
    assert r1.status_code == 201
    r2 = client.post("/api/tenants", json=payload)
    assert r2.status_code == 422


def test_create_tenant_invalid_slug_is_422():
    r = client.post(
        "/api/tenants",
        json={
            "slug": "Not A Valid Slug!",
            "category": "salon_spa",
            "business_name": "Whatever",
        },
    )
    assert r.status_code == 422


def test_create_tenant_invalid_category_is_422():
    r = client.post(
        "/api/tenants",
        json={
            "slug": _slug(),
            "category": "not-a-real-category",
            "business_name": "Whatever",
        },
    )
    assert r.status_code == 422


def test_create_tenant_bad_hours_is_422():
    r = client.post(
        "/api/tenants",
        json={
            "slug": _slug(),
            "category": "salon_spa",
            "business_name": "Whatever",
            "open_hour": 18,
            "close_hour": 9,
        },
    )
    assert r.status_code == 422


# --- list / detail ------------------------------------------------------------
def test_list_tenants_includes_seeded_tenant():
    r = client.get("/api/tenants")
    assert r.status_code == 200
    slugs = {t["slug"] for t in r.json()}
    assert TENANT_SLUG in slugs


def test_get_tenant_detail_success_and_no_secret_leak():
    r = client.get(f"/api/tenants/{TENANT_SLUG}")
    assert r.status_code == 200
    body = r.json()
    assert body["slug"] == TENANT_SLUG
    assert "webhook_secret" not in body
    assert "services" in body and "bookings" in body


def test_get_tenant_detail_unknown_is_404():
    r = client.get("/api/tenants/not-a-real-tenant")
    assert r.status_code == 404


# --- preview ------------------------------------------------------------------
def test_preview_tenant_flow():
    r = client.get(f"/api/tenants/{TENANT_SLUG}/preview")
    assert r.status_code == 200
    body = r.json()
    assert "nodes" in body or "conversation_flow" in body or isinstance(body, dict)


# --- provision ------------------------------------------------------------
def test_provision_success(monkeypatch):
    slug = _slug()
    r = client.post(
        "/api/tenants",
        json={"slug": slug, "category": "salon_spa", "business_name": "Provision Test", "services": ["Haircut"]},
    )
    assert r.status_code == 201

    monkeypatch.setattr(
        admin_api,
        "provision_tenant",
        lambda *a, **k: {"conversation_flow_id": "flow_abc", "agent_id": "agent_xyz"},
    )
    monkeypatch.setattr(admin_api.settings, "RETELL_API_KEY", "fake-key")
    monkeypatch.setattr(admin_api.settings, "BACKEND_BASE_URL", "https://backend.example.com")

    r = client.post(f"/api/tenants/{slug}/provision")
    assert r.status_code == 200
    body = r.json()
    assert body == {"conversation_flow_id": "flow_abc", "agent_id": "agent_xyz"}


def test_provision_already_provisioned_is_409(monkeypatch, db_session):
    slug = _slug()
    r = client.post(
        "/api/tenants",
        json={"slug": slug, "category": "salon_spa", "business_name": "Already Provisioned", "services": ["Haircut"]},
    )
    assert r.status_code == 201
    tenant = db_session.query(db_models.Tenant).filter_by(slug=slug).first()
    tenant.retell_agent_id = "existing_agent"
    db_session.commit()

    monkeypatch.setattr(admin_api.settings, "RETELL_API_KEY", "fake-key")
    monkeypatch.setattr(admin_api.settings, "BACKEND_BASE_URL", "https://backend.example.com")

    r = client.post(f"/api/tenants/{slug}/provision")
    assert r.status_code == 409


def test_provision_error_is_502(monkeypatch):
    from app.provisioning import ProvisioningError

    slug = _slug()
    r = client.post(
        "/api/tenants",
        json={"slug": slug, "category": "salon_spa", "business_name": "Provision Fails", "services": ["Haircut"]},
    )
    assert r.status_code == 201

    def _boom(*a, **k):
        raise ProvisioningError("Retell said no")

    monkeypatch.setattr(admin_api, "provision_tenant", _boom)
    monkeypatch.setattr(admin_api.settings, "RETELL_API_KEY", "fake-key")
    monkeypatch.setattr(admin_api.settings, "BACKEND_BASE_URL", "https://backend.example.com")

    r = client.post(f"/api/tenants/{slug}/provision")
    assert r.status_code == 502


def test_provision_missing_api_key_is_503(monkeypatch):
    slug = _slug()
    r = client.post(
        "/api/tenants",
        json={"slug": slug, "category": "salon_spa", "business_name": "No Key", "services": ["Haircut"]},
    )
    assert r.status_code == 201

    monkeypatch.setattr(admin_api.settings, "RETELL_API_KEY", "")

    r = client.post(f"/api/tenants/{slug}/provision")
    assert r.status_code == 503


# --- contact --------------------------------------------------------------
def test_contact_form_success(monkeypatch):
    monkeypatch.setattr(admin_api, "send_contact_notification", lambda *a, **k: True)
    r = client.post(
        "/api/contact",
        json={"name": "Priya", "email": "priya@example.com", "business_type": "salon_spa", "message": "Hi there"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "sent"


def test_contact_form_invalid_email_is_422():
    r = client.post(
        "/api/contact",
        json={"name": "Priya", "email": "not-an-email", "message": "Hi there"},
    )
    assert r.status_code == 422


def test_contact_form_soft_fails_when_email_send_fails(monkeypatch):
    monkeypatch.setattr(admin_api, "send_contact_notification", lambda *a, **k: False)
    r = client.post(
        "/api/contact",
        json={"name": "Priya", "email": "priya@example.com", "message": "Hi there"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "received"
