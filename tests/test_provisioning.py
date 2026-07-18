"""Tests for app/provisioning.py using httpx.MockTransport -- no test here
ever makes a real network call to the Retell API.
"""
import json
import uuid

import httpx
import pytest

from app.db_models import Service, Tenant
from app.provisioning import ProvisioningError, provision_tenant
from app.templates.registry import get_template


@pytest.fixture
def tenant(db_session):
    t = Tenant(
        slug=f"provisioning-test-{uuid.uuid4().hex[:8]}",
        category="dental_medical",
        business_name="Provisioning Test Dental",
        timezone="Asia/Kolkata",
        open_hour=9,
        close_hour=18,
        open_weekdays=[0, 1, 2, 3, 4, 5],
        address="1 Test Street",
        webhook_secret="secret123",
        booking_reference_prefix="PTD",
    )
    db_session.add(t)
    db_session.commit()
    db_session.add(Service(tenant_id=t.id, name="Dental Cleaning", sort_order=0))
    db_session.commit()
    db_session.refresh(t)
    return t


def test_provision_tenant_success(tenant):
    template = get_template("dental_medical")
    requests_seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests_seen.append(request)
        if request.url.path == "/create-conversation-flow":
            return httpx.Response(201, json={"conversation_flow_id": "flow_123"})
        if request.url.path == "/create-agent":
            return httpx.Response(201, json={"agent_id": "agent_456"})
        return httpx.Response(404)

    client = httpx.Client(base_url="https://api.retellai.com", transport=httpx.MockTransport(handler))
    result = provision_tenant(
        tenant, template, "https://backend.example.com", "fake-api-key", client=client
    )

    assert result == {"conversation_flow_id": "flow_123", "agent_id": "agent_456"}
    assert [r.url.path for r in requests_seen] == ["/create-conversation-flow", "/create-agent"]
    for req in requests_seen:
        assert req.headers["authorization"] == "Bearer fake-api-key"

    agent_payload = json.loads(requests_seen[1].content)
    assert agent_payload["response_engine"]["conversation_flow_id"] == "flow_123"
    assert agent_payload["voice_id"] == template.default_voice_id


def test_provision_tenant_flow_creation_failure_raises(tenant):
    template = get_template("dental_medical")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"error": "bad request"})

    client = httpx.Client(base_url="https://api.retellai.com", transport=httpx.MockTransport(handler))
    with pytest.raises(ProvisioningError):
        provision_tenant(tenant, template, "https://backend.example.com", "fake-api-key", client=client)


def test_provision_tenant_agent_creation_failure_raises(tenant):
    template = get_template("dental_medical")

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/create-conversation-flow":
            return httpx.Response(201, json={"conversation_flow_id": "flow_123"})
        return httpx.Response(500, json={"error": "server error"})

    client = httpx.Client(base_url="https://api.retellai.com", transport=httpx.MockTransport(handler))
    with pytest.raises(ProvisioningError):
        provision_tenant(tenant, template, "https://backend.example.com", "fake-api-key", client=client)


def test_provision_tenant_invalid_flow_raises_before_any_http_call(tenant):
    """A tenant/template combo that fails validate_flow() must never reach
    the network layer -- simulated here by an empty service list on both
    the tenant and the template default_services."""
    from dataclasses import replace

    template = replace(get_template("dental_medical"), default_services=())
    tenant.services = []

    def handler(request: httpx.Request) -> httpx.Response:  # pragma: no cover
        raise AssertionError("HTTP layer should not be reached")

    client = httpx.Client(base_url="https://api.retellai.com", transport=httpx.MockTransport(handler))
    with pytest.raises(ValueError):
        provision_tenant(tenant, template, "https://backend.example.com", "fake-api-key", client=client)
