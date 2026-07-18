"""Call-event persistence: upsert one CallEvent row per call_id as Retell
posts the call_started / call_ended / call_analyzed lifecycle events.

Best-effort, exactly like the booking notifiers -- a malformed event or a
write error is logged and swallowed, never raised, so it can't disturb the
webhook response Retell expects.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from .db_models import CallEvent, Tenant

logger = logging.getLogger("agent.call_events")

_STATUS_BY_EVENT = {
    "call_started": "ongoing",
    "call_ended": "ended",
    "call_analyzed": "analyzed",
}


def _ms_to_iso(ms: object) -> Optional[str]:
    """Retell sends epoch milliseconds; store as ISO8601 UTC text."""
    try:
        return datetime.fromtimestamp(float(ms) / 1000, tz=timezone.utc).isoformat(timespec="seconds")
    except (TypeError, ValueError):
        return None


def record_call_event(db: Session, tenant: Tenant, body: dict) -> Optional[CallEvent]:
    """Create or update the CallEvent for this call. Returns it, or None on failure."""
    try:
        event = str(body.get("event", "")) or "unknown"
        call = body.get("call") or {}
        call_id = str(call.get("call_id") or "").strip()
        if not call_id:
            return None

        row = (
            db.query(CallEvent)
            .filter(CallEvent.tenant_id == tenant.id, CallEvent.call_id == call_id)
            .first()
        )
        if row is None:
            row = CallEvent(tenant_id=tenant.id, call_id=call_id)
            db.add(row)

        # Advance status monotonically (analyzed > ended > ongoing).
        new_status = _STATUS_BY_EVENT.get(event)
        rank = {"ongoing": 0, "ended": 1, "analyzed": 2}
        if new_status and rank.get(new_status, 0) >= rank.get(row.call_status, 0):
            row.call_status = new_status

        # Overwrite only when the event actually carries the field.
        if call.get("direction"):
            row.direction = str(call["direction"])
        if call.get("from_number"):
            row.from_number = str(call["from_number"])
        if call.get("to_number"):
            row.to_number = str(call["to_number"])
        if call.get("disconnection_reason"):
            row.disconnection_reason = str(call["disconnection_reason"])
        if call.get("transcript"):
            row.transcript = str(call["transcript"])
        if call.get("start_timestamp"):
            row.started_at = _ms_to_iso(call["start_timestamp"]) or row.started_at
        if call.get("end_timestamp"):
            row.ended_at = _ms_to_iso(call["end_timestamp"]) or row.ended_at

        duration_ms = call.get("duration_ms")
        if duration_ms is not None:
            try:
                row.duration_seconds = int(round(float(duration_ms) / 1000))
            except (TypeError, ValueError):
                pass

        analysis = call.get("call_analysis") or {}
        if analysis.get("call_summary"):
            row.summary = str(analysis["call_summary"])
        if analysis.get("user_sentiment"):
            row.user_sentiment = str(analysis["user_sentiment"])
        if analysis.get("call_successful") is not None:
            row.call_successful = bool(analysis["call_successful"])

        db.commit()
        db.refresh(row)
        return row
    except Exception as exc:  # noqa: BLE001 - never let logging a call break the webhook
        db.rollback()
        logger.error("Failed to record call event for tenant %s: %s", tenant.slug, exc)
        return None
