"""Tests for app/flow_builder.py -- validates that the parameterized flow
skeleton renders correctly for a real tenant, without ever calling the
Retell API. Uses the shared in-memory test DB from tests/conftest.py.
"""
import uuid

import pytest

from app.db_models import Service, Tenant
from app.flow_builder import build_flow, validate_flow
from app.templates.registry import CATEGORY_TEMPLATES, get_template

_EXPECTED_NODE_IDS = {
    "node_welcome", "node_faq", "node_emergency", "node_collect_details",
    "node_extract", "node_check_availability", "node_suggest_alt",
    "node_confirm", "node_book", "node_booking_success", "node_booking_failed",
    "node_transfer", "node_transfer_failed", "node_goodbye", "node_end",
}


@pytest.fixture
def dental_tenant(db_session):
    tenant = Tenant(
        slug=f"flow-test-{uuid.uuid4().hex[:8]}",
        category="dental_medical",
        business_name="Flow Test Dental",
        timezone="Asia/Kolkata",
        open_hour=9,
        close_hour=18,
        open_weekdays=[0, 1, 2, 3, 4, 5],
        address="1 Test Street",
        webhook_secret="tok_test_123",
        booking_reference_prefix="FTD",
        extra_facts={"consultation_fee": "500 rupees", "walk_ins": "Accepted"},
    )
    db_session.add(tenant)
    db_session.commit()
    names = ["Dental Cleaning", "Root Canal Treatment", "Teeth Whitening"]
    for i, name in enumerate(names):
        db_session.add(Service(tenant_id=tenant.id, name=name, sort_order=i))
    db_session.commit()
    db_session.refresh(tenant)
    return tenant


def test_build_flow_validates_cleanly(dental_tenant):
    template = get_template("dental_medical")
    flow = build_flow(dental_tenant, template, "https://backend.example.com")
    validate_flow(flow)  # must not raise


def test_node_ids_match_skeleton_exactly(dental_tenant):
    template = get_template("dental_medical")
    flow = build_flow(dental_tenant, template, "https://backend.example.com")
    node_ids = {n["id"] for n in flow["nodes"]}
    assert node_ids == _EXPECTED_NODE_IDS


def test_global_prompt_contains_tenant_facts_not_placeholders(dental_tenant):
    template = get_template("dental_medical")
    flow = build_flow(dental_tenant, template, "https://backend.example.com")
    prompt = flow["global_prompt"]
    assert "Flow Test Dental" in prompt
    assert "1 Test Street" in prompt
    assert "500 rupees" in prompt
    assert "$" not in prompt  # no unresolved $identifier placeholders remain


def test_urgent_branch_prose_resolved_not_left_as_placeholder(dental_tenant):
    template = get_template("dental_medical")
    flow = build_flow(dental_tenant, template, "https://backend.example.com")
    emergency_node = next(n for n in flow["nodes"] if n["id"] == "node_emergency")
    text = emergency_node["instruction"]["text"]
    assert "$working_hours_short" not in text
    assert "Flow Test Dental" in text
    assert "9:00 AM to 6:00 PM" in text


def test_tool_urls_are_tenant_scoped_and_well_formed(dental_tenant):
    template = get_template("dental_medical")
    flow = build_flow(dental_tenant, template, "https://backend.example.com")
    check_tool, book_tool = flow["tools"]
    assert check_tool["url"] == (
        f"https://backend.example.com/webhook/{dental_tenant.slug}/check-availability?token=tok_test_123"
    )
    assert book_tool["url"] == (
        f"https://backend.example.com/webhook/{dental_tenant.slug}/book-appointment?token=tok_test_123"
    )


def test_service_enum_reflects_active_tenant_services(dental_tenant):
    template = get_template("dental_medical")
    flow = build_flow(dental_tenant, template, "https://backend.example.com")
    check_tool, book_tool = flow["tools"]
    expected = ["Dental Cleaning", "Root Canal Treatment", "Teeth Whitening"]
    assert check_tool["parameters"]["properties"]["service"]["enum"] == expected
    assert book_tool["parameters"]["properties"]["service"]["enum"] == expected
    extract_node = next(n for n in flow["nodes"] if n["id"] == "node_extract")
    service_var = next(v for v in extract_node["variables"] if v["name"] == "service")
    assert service_var["choices"] == expected


def test_falls_back_to_template_default_services_when_tenant_has_none(db_session):
    tenant = Tenant(
        slug=f"flow-test-nosvc-{uuid.uuid4().hex[:8]}",
        category="dental_medical",
        business_name="No Services Yet Dental",
        timezone="Asia/Kolkata",
        open_hour=9,
        close_hour=18,
        open_weekdays=[0, 1, 2, 3, 4, 5],
        webhook_secret="tok_test_456",
        booking_reference_prefix="NSY",
    )
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)

    template = get_template("dental_medical")
    flow = build_flow(tenant, template, "https://backend.example.com")
    validate_flow(flow)
    check_tool = flow["tools"][0]
    assert check_tool["parameters"]["properties"]["service"]["enum"] == [
        d.name for d in template.default_services
    ]


class _FakeTenant:
    slug = "x"
    business_name = "X"
    timezone = "Asia/Kolkata"
    open_hour = 9
    close_hour = 18
    open_weekdays = [0, 1, 2, 3, 4, 5]
    address = ""
    transfer_number = ""
    webhook_secret = "t"
    extra_facts: dict = {}
    services: list = []


def test_validate_flow_rejects_missing_node():
    template = get_template("dental_medical")
    flow = build_flow(_FakeTenant(), template, "https://backend.example.com")
    flow["nodes"] = [n for n in flow["nodes"] if n["id"] != "node_goodbye"]
    with pytest.raises(ValueError):
        validate_flow(flow)


def test_validate_flow_rejects_empty_service_enum():
    template = get_template("dental_medical")
    flow = build_flow(_FakeTenant(), template, "https://backend.example.com")
    flow["tools"][1]["parameters"]["properties"]["service"]["enum"] = []
    with pytest.raises(ValueError):
        validate_flow(flow)


@pytest.mark.parametrize("category_key", sorted(CATEGORY_TEMPLATES))
def test_every_registered_category_builds_and_validates_cleanly(category_key):
    """Phase C parity check: every category (dental, salon/spa, restaurant,
    home services) renders onto the exact same 14-node skeleton with no
    leftover $identifier placeholders."""
    template = get_template(category_key)
    flow = build_flow(_FakeTenant(), template, "https://backend.example.com")
    validate_flow(flow)
    node_ids = {n["id"] for n in flow["nodes"]}
    assert node_ids == _EXPECTED_NODE_IDS
    assert "$" not in flow["global_prompt"]
    emergency_node = next(n for n in flow["nodes"] if n["id"] == "node_emergency")
    assert "$" not in emergency_node["instruction"]["text"]


def test_restaurant_extra_slots_appended_to_extract_and_book_tool():
    template = get_template("restaurant")
    flow = build_flow(_FakeTenant(), template, "https://backend.example.com")

    extract_node = next(n for n in flow["nodes"] if n["id"] == "node_extract")
    var_names = {v["name"] for v in extract_node["variables"]}
    assert {"party_size", "occasion"} <= var_names

    book_tool = flow["tools"][1]
    props = book_tool["parameters"]["properties"]
    assert "party_size" in props and "occasion" in props
    assert "party_size" in book_tool["parameters"]["required"]
    assert "occasion" not in book_tool["parameters"]["required"]


def test_dental_has_no_extra_slots_and_others_do():
    assert get_template("dental_medical").extra_slots == ()
    assert get_template("salon_spa").extra_slots
    assert get_template("restaurant").extra_slots
    assert get_template("home_services").extra_slots
