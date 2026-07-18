"""Renders a tenant-specific RetellAI Conversation Flow JSON from a category
template + tenant DB row, ready to POST to the Retell API.

Reuses the exact node/edge/tool graph from the live-tested dental flow
(app/templates/skeleton.py) -- only prose text and small data lists
(services, working hours, facts) are substituted per tenant. Node IDs,
edge IDs, and the overall graph shape never change, so a rendered flow can
always be diffed against the original retell_conversation_flow.json for a
parity review before anything is sent to the live Retell API.

Templating uses stdlib string.Template on already-parsed Python dicts (not
raw JSON text), so tenant-authored text containing quotes or newlines can
never corrupt the JSON structure. substitute() (not safe_substitute()) is
used deliberately: a $identifier in the skeleton with no matching mapping
key is a bug in this module, and should raise loudly at build time rather
than ship a literal "$foo" into a live prompt.
"""
from __future__ import annotations

import copy
from string import Template
from typing import Any

from .db_models import Tenant
from .templates.base import CategoryTemplate
from .templates.skeleton import FLOW_SKELETON, SERVICE_ENUM_SENTINEL

WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

_EXPECTED_NODE_IDS = {
    "node_welcome", "node_faq", "node_emergency", "node_collect_details",
    "node_extract", "node_check_availability", "node_suggest_alt",
    "node_confirm", "node_book", "node_booking_success", "node_booking_failed",
    "node_transfer", "node_transfer_failed", "node_goodbye", "node_end",
}


def _format_hour(hour: int) -> str:
    period = "AM" if hour < 12 else "PM"
    display = hour % 12 or 12
    return f"{display}:00 {period}"


def _format_open_days(open_weekdays: list[int]) -> str:
    days = sorted(open_weekdays)
    if not days:
        return "by appointment only"
    names = [WEEKDAY_NAMES[d] for d in days]
    if len(names) == 1:
        return names[0]
    if days == list(range(days[0], days[0] + len(days))):
        return f"{names[0]} to {names[-1]}"
    return ", ".join(names[:-1]) + f" and {names[-1]}"


def _working_hours_sentence(open_hour: int, close_hour: int, open_weekdays: list[int]) -> str:
    days_sentence = _format_open_days(open_weekdays)
    hours_sentence = f"{_format_hour(open_hour)} to {_format_hour(close_hour)}"
    closed = sorted(set(range(7)) - set(open_weekdays))
    closed_sentence = ""
    if closed:
        closed_names = ", ".join(f"{WEEKDAY_NAMES[d]}s" for d in closed)
        closed_sentence = f" Closed on {closed_names}."
    return f"{days_sentence}, {hours_sentence}.{closed_sentence}"


def _working_hours_short(open_hour: int, close_hour: int, open_weekdays: list[int]) -> str:
    return f"{_format_open_days(open_weekdays)}, {_format_hour(open_hour)} to {_format_hour(close_hour)}"


def _facts_bullets(template: CategoryTemplate, extra_facts: dict) -> str:
    lines = [f"- {label}: {extra_facts[key]}" for key, label in template.fact_bullet_labels if extra_facts.get(key)]
    return "\n".join(lines)


def _substitute(obj: Any, mapping: dict) -> Any:
    if isinstance(obj, str):
        return Template(obj).substitute(mapping)
    if isinstance(obj, dict):
        return {k: _substitute(v, mapping) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_substitute(v, mapping) for v in obj]
    return obj


def _inject_service_enum(obj: Any, service_names: list[str]) -> Any:
    if isinstance(obj, dict):
        return {k: _inject_service_enum(v, service_names) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_inject_service_enum(v, service_names) for v in obj]
    if obj == SERVICE_ENUM_SENTINEL:
        return list(service_names)
    return obj


def _webhook_url(backend_base_url: str, tenant_slug: str, path: str, token: str) -> str:
    url = f"{backend_base_url.rstrip('/')}/webhook/{tenant_slug}/{path}"
    return f"{url}?token={token}" if token else url


def build_flow(tenant: Tenant, template: CategoryTemplate, backend_base_url: str) -> dict:
    """Render this tenant's Conversation Flow JSON."""
    active_services = sorted((s for s in tenant.services if s.is_active), key=lambda s: s.sort_order)
    service_names = [s.name for s in active_services] or [d.name for d in template.default_services]

    # Pass 1: resolve the category template's own prose (which may itself
    # reference tenant facts like working hours) against tenant-level values.
    base_mapping = {
        "business_name": tenant.business_name,
        "agent_persona_name": template.agent_persona_name,
        "role_sentence": template.role_sentence,
        "booking_noun": template.booking_noun,
        "customer_noun": template.customer_noun,
        "service_noun": template.service_noun,
        "staff_noun": template.staff_noun,
        "scope_disclaimer": template.scope_disclaimer,
        "escalation_priority_note": template.escalation_priority_note,
        "working_hours_sentence": _working_hours_sentence(tenant.open_hour, tenant.close_hour, tenant.open_weekdays),
        "working_hours_short": _working_hours_short(tenant.open_hour, tenant.close_hour, tenant.open_weekdays),
        "location_sentence": tenant.address or "available on request",
        "services_sentence": ", ".join(service_names),
        "facts_bullets": _facts_bullets(template, tenant.extra_facts or {}),
        "check_availability_url": _webhook_url(backend_base_url, tenant.slug, "check-availability", tenant.webhook_secret),
        "book_appointment_url": _webhook_url(backend_base_url, tenant.slug, "book-appointment", tenant.webhook_secret),
    }

    def _resolve(text: str) -> str:
        return Template(text).substitute(base_mapping)

    # Pass 2: fold in the urgent branch's own text, pre-resolved.
    full_mapping = dict(base_mapping)
    full_mapping["urgent_node_name"] = template.urgent_branch.node_name
    full_mapping["urgent_instruction_text"] = _resolve(template.urgent_branch.instruction_text)
    full_mapping["urgent_welcome_trigger"] = _resolve(template.urgent_branch.welcome_trigger_prompt)
    full_mapping["urgent_faq_trigger"] = _resolve(template.urgent_branch.faq_trigger_prompt)
    full_mapping["urgent_book_instead_prompt"] = _resolve(template.urgent_branch.book_instead_prompt)

    flow = _substitute(copy.deepcopy(FLOW_SKELETON), full_mapping)
    flow = _inject_service_enum(flow, service_names)

    flow["default_dynamic_variables"] = {
        "business_name": tenant.business_name,
        "human_agent_number": tenant.transfer_number or "",
    }

    # Category-specific slots beyond the fixed 6 (Phase C categories) land in
    # both the extraction node and the booking tool's schema, so Retell
    # actually captures and sends them as args -- app/bookings.py's
    # compute_extra_fields() then stores anything beyond the fixed booking
    # columns with zero backend code changes.
    if template.extra_slots:
        extract_node = next(n for n in flow["nodes"] if n["id"] == "node_extract")
        book_params = flow["tools"][1]["parameters"]
        for slot in template.extra_slots:
            extract_node["variables"].append(dict(slot))
            book_params["properties"][slot["name"]] = {
                "type": slot.get("type", "string"),
                "description": slot["description"],
            }
            if slot.get("required"):
                book_params["required"].append(slot["name"])

    return flow


def validate_flow(flow: dict) -> None:
    """Structural sanity checks run before a flow is ever sent to Retell."""
    node_ids = {n["id"] for n in flow["nodes"]}
    if node_ids != _EXPECTED_NODE_IDS:
        missing = _EXPECTED_NODE_IDS - node_ids
        extra = node_ids - _EXPECTED_NODE_IDS
        raise ValueError(f"Flow node-id set doesn't match the skeleton. missing={missing} extra={extra}")

    for tool in flow["tools"]:
        if not tool["url"].startswith("http"):
            raise ValueError(f"Tool '{tool['name']}' has an invalid URL: {tool['url']}")

    service_enum = flow["tools"][1]["parameters"]["properties"]["service"]["enum"]
    if not service_enum:
        raise ValueError("No active services -- the service enum would be empty.")
