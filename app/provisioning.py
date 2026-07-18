"""Creates a tenant's RetellAI conversation flow + agent via the Retell API.

NOTE: the request/response field names below (response_engine,
conversation_flow_id, agent_name, ...) follow Retell's public API shape as
documented; they have not been re-verified against a live call in *this*
session. Always run scripts/create_tenant.py with --dry-run first to review
the built flow, and treat the first real (non-dry-run) provisioning call
for a new category as a manual smoke test, not a guaranteed-correct
operation -- confirm the resulting agent in the Retell dashboard before
pointing a phone number at it.
"""
from __future__ import annotations

from typing import Optional

import httpx

from .db_models import Tenant
from .flow_builder import build_flow, validate_flow
from .templates.base import CategoryTemplate


class ProvisioningError(RuntimeError):
    pass


def provision_tenant(
    tenant: Tenant,
    template: CategoryTemplate,
    backend_base_url: str,
    api_key: str,
    *,
    api_base: str = "https://api.retellai.com",
    client: Optional[httpx.Client] = None,
) -> dict:
    """Build, validate, and create a NEW conversation flow + agent in Retell.

    Always creates independent resources -- never mutates an existing
    flow/agent, since Retell's update endpoints haven't been exercised by
    this codebase. Returns {"conversation_flow_id": ..., "agent_id": ...}.
    """
    flow = build_flow(tenant, template, backend_base_url)
    validate_flow(flow)

    owns_client = client is None
    http = client or httpx.Client(base_url=api_base, timeout=30.0)
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    try:
        flow_resp = http.post("/create-conversation-flow", json=flow, headers=headers)
        if flow_resp.status_code >= 400:
            raise ProvisioningError(
                f"create-conversation-flow failed ({flow_resp.status_code}): {flow_resp.text}"
            )
        conversation_flow_id = flow_resp.json()["conversation_flow_id"]

        agent_payload = {
            "response_engine": {
                "type": "conversation-flow",
                "conversation_flow_id": conversation_flow_id,
            },
            "voice_id": template.default_voice_id,
            "agent_name": f"{tenant.business_name} ({tenant.slug})",
        }
        agent_resp = http.post("/create-agent", json=agent_payload, headers=headers)
        if agent_resp.status_code >= 400:
            raise ProvisioningError(f"create-agent failed ({agent_resp.status_code}): {agent_resp.text}")
        agent_id = agent_resp.json()["agent_id"]
    finally:
        if owns_client:
            http.close()

    return {"conversation_flow_id": conversation_flow_id, "agent_id": agent_id}
