"""FastAPI backend for the QuensultingAI Dental Clinic voice agent.

Endpoints (all called by RetellAI):
  GET  /health                       -> liveness check
  POST /webhook/check-availability   -> custom tool: is a slot bookable?
  POST /webhook/book-appointment     -> custom tool: save + notify, returns ref
  POST /webhook/retell-events        -> agent-level call events (optional logging)

The two custom-tool endpoints return plain JSON objects; the RetellAI flow maps
fields from these responses into dynamic variables (see retell_conversation_flow.json).
"""
from __future__ import annotations

import logging
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request

from .config import settings
from .models import (
    AvailabilityResponse,
    BookAppointmentArgs,
    BookingResponse,
    CheckAvailabilityArgs,
)
from .notifications import fire_booking_webhook, send_confirmation_email
from .sheets import append_booking
from .utils import (
    generate_booking_reference,
    humanize_datetime,
    now_clinic,
    parse_datetime,
    suggest_slots,
    within_working_hours,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(name)s  %(message)s",
)
logger = logging.getLogger("dental.api")

app = FastAPI(title="QuensultingAI Dental Voice Agent", version="1.0.0")


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _verify_token(request: Request) -> None:
    """Reject calls that don't carry the shared secret (if one is configured).

    Retell appends it as a query param on the tool URL: ...?token=SECRET
    """
    if not settings.WEBHOOK_SECRET:
        return  # protection disabled (fine for local testing)
    token = request.query_params.get("token") or request.headers.get("x-webhook-token")
    if token != settings.WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Invalid or missing token")


async def _extract_args(request: Request) -> tuple[dict, dict]:
    """Return (args, call) from a Retell tool-call envelope.

    Retell posts {"call": {...}, "name": "...", "args": {...}} by default. We
    also accept a flat body (args_at_root=true) so the endpoint is robust.
    """
    try:
        body = await request.json()
    except Exception:  # noqa: BLE001
        body = {}
    if isinstance(body, dict) and "args" in body and isinstance(body["args"], dict):
        return body["args"], body.get("call", {}) or {}
    return body if isinstance(body, dict) else {}, {}


# --------------------------------------------------------------------------- #
# Routes
# --------------------------------------------------------------------------- #
@app.get("/health")
def health() -> dict:
    return {"status": "ok", "clinic": settings.CLINIC_NAME, "time": now_clinic().isoformat()}


@app.post("/webhook/check-availability", response_model=AvailabilityResponse)
async def check_availability(request: Request) -> AvailabilityResponse:
    _verify_token(request)
    args, _call = await _extract_args(request)
    data = CheckAvailabilityArgs(**{k: args.get(k) for k in ("preferred_datetime", "service")})

    dt = parse_datetime(data.preferred_datetime)
    if dt is None:
        # We couldn't understand the time — treat as unavailable and re-ask.
        return AvailabilityResponse(
            available="false",
            reason="I couldn't quite catch that date and time.",
            suggested_slots="",
        )

    ok, reason = within_working_hours(dt)
    logger.info("Availability check '%s' -> %s (%s)", data.preferred_datetime, ok, reason)
    return AvailabilityResponse(
        available="true" if ok else "false",
        reason=reason,
        suggested_slots="" if ok else suggest_slots(dt),
    )


@app.post("/webhook/book-appointment", response_model=BookingResponse)
async def book_appointment(request: Request) -> BookingResponse:
    _verify_token(request)
    args, call = await _extract_args(request)

    required = ("patient_name", "phone_number", "service", "preferred_datetime")
    missing = [f for f in required if not str(args.get(f, "")).strip()]
    if missing:
        logger.error("Booking rejected, missing fields: %s", missing)
        return BookingResponse(
            status="failed",
            message=f"Missing required details: {', '.join(missing)}.",
        )

    data = BookAppointmentArgs(
        patient_name=str(args["patient_name"]).strip(),
        phone_number=str(args["phone_number"]).strip(),
        service=str(args["service"]).strip(),
        preferred_datetime=str(args["preferred_datetime"]).strip(),
        patient_email=(args.get("patient_email") or "").strip(),
        notes=(args.get("notes") or "").strip(),
    )

    dt = parse_datetime(data.preferred_datetime)
    confirmed = humanize_datetime(dt, fallback=data.preferred_datetime)
    reference = generate_booking_reference()

    record = {
        "timestamp": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "booking_reference": reference,
        "patient_name": data.patient_name,
        "phone_number": data.phone_number,
        "patient_email": data.patient_email,
        "service": data.service,
        "preferred_datetime": data.preferred_datetime,
        "confirmed_datetime": confirmed,
        "notes": data.notes,
        "call_id": (call or {}).get("call_id", ""),
        "status": "confirmed",
    }

    # 1) Persist — this is the source of truth. If it fails, the booking fails.
    if not append_booking(record):
        return BookingResponse(
            status="failed",
            message="We couldn't save the booking to our system.",
        )

    # 2) Best-effort notifications (never block a successful booking). The
    #    notifiers catch their own errors, but we wrap them here too so an
    #    unexpected exception can't undo a booking that's already persisted.
    for notify in (send_confirmation_email, fire_booking_webhook):
        try:
            notify(record)
        except Exception as exc:  # noqa: BLE001
            logger.error("Notification %s failed: %s", notify.__name__, exc)

    logger.info("Booking confirmed: %s for %s", reference, data.patient_name)
    return BookingResponse(
        status="success",
        booking_reference=reference,
        confirmed_datetime=confirmed,
        message="Appointment booked.",
    )


@app.post("/webhook/retell-events")
async def retell_events(request: Request) -> dict:
    """Optional: log agent-level call lifecycle events (started/ended/analyzed).

    Configure this URL as the agent Webhook in the Retell dashboard. Signature
    verification can be added with the Retell SDK's Retell.verify() helper.
    """
    try:
        body = await request.json()
    except Exception:  # noqa: BLE001
        body = {}
    event = body.get("event", "unknown")
    call_id = (body.get("call") or {}).get("call_id", "")
    logger.info("Retell event '%s' for call %s", event, call_id)
    return {"received": True}
