"""FastAPI backend for the multi-tenant AI receptionist platform.

Endpoints (all called by RetellAI, tenant-scoped by path segment):
  GET  /health                                          -> liveness check
  POST /webhook/{tenant_slug}/check-availability         -> custom tool: is a slot bookable?
  POST /webhook/{tenant_slug}/book-appointment           -> custom tool: save + notify, returns ref
  POST /webhook/{tenant_slug}/retell-events              -> agent-level call events (optional logging)

The two custom-tool endpoints return plain JSON objects; each tenant's
RetellAI flow maps fields from these responses into dynamic variables.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from sqlalchemy.orm import Session
from starlette.responses import FileResponse
from starlette.staticfiles import StaticFiles

from .admin_api import router as admin_router
from .bookings import compute_extra_fields, save_booking
from .call_events import record_call_event
from .portal_api import router as portal_router
from .db import get_db, init_db
from .db_models import Tenant
from .models import (
    AvailabilityResponse,
    BookAppointmentArgs,
    BookingResponse,
    CheckAvailabilityArgs,
)
from .notifications import fire_booking_webhook, send_confirmation_email
from .sheets import append_booking
from .tenancy import get_tenant_or_404
from .utils import (
    generate_booking_reference,
    humanize_datetime,
    parse_datetime,
    suggest_slots,
    within_working_hours,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(name)s  %(message)s",
)
logger = logging.getLogger("agent.api")

app = FastAPI(title="AI Receptionist Platform", version="2.0.0")
app.include_router(admin_router)
app.include_router(portal_router)


@app.on_event("startup")
def _on_startup() -> None:
    init_db()


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _verify_token(request: Request, tenant: Tenant) -> None:
    """Reject calls that don't carry the tenant's shared secret (if one is set).

    Retell appends it as a query param on the tool URL: ...?token=SECRET
    """
    if not tenant.webhook_secret:
        return  # protection disabled (fine for local testing)
    token = request.query_params.get("token") or request.headers.get("x-webhook-token")
    if token != tenant.webhook_secret:
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
    return {"status": "ok", "time": datetime.now(timezone.utc).isoformat()}


@app.post("/webhook/{tenant_slug}/check-availability", response_model=AvailabilityResponse)
async def check_availability(
    tenant_slug: str, request: Request, db: Session = Depends(get_db)
) -> AvailabilityResponse:
    tenant = get_tenant_or_404(db, tenant_slug)
    _verify_token(request, tenant)
    args, _call = await _extract_args(request)
    data = CheckAvailabilityArgs(**{k: args.get(k) for k in ("preferred_datetime", "service")})

    dt = parse_datetime(data.preferred_datetime, tz=tenant.timezone)
    if dt is None:
        # We couldn't understand the time — treat as unavailable and re-ask.
        return AvailabilityResponse(
            available="false",
            reason="I couldn't quite catch that date and time.",
            suggested_slots="",
        )

    ok, reason = within_working_hours(
        dt, tenant.open_hour, tenant.close_hour, tenant.open_weekdays, tenant.timezone
    )
    logger.info("[%s] Availability check '%s' -> %s (%s)", tenant.slug, data.preferred_datetime, ok, reason)
    return AvailabilityResponse(
        available="true" if ok else "false",
        reason=reason,
        suggested_slots="" if ok else suggest_slots(
            dt, tenant.open_hour, tenant.close_hour, tenant.open_weekdays, tenant.timezone
        ),
    )


@app.post("/webhook/{tenant_slug}/book-appointment", response_model=BookingResponse)
async def book_appointment(
    tenant_slug: str, request: Request, db: Session = Depends(get_db)
) -> BookingResponse:
    tenant = get_tenant_or_404(db, tenant_slug)
    _verify_token(request, tenant)
    args, call = await _extract_args(request)

    required = ("patient_name", "phone_number", "service", "preferred_datetime")
    missing = [f for f in required if not str(args.get(f, "")).strip()]
    if missing:
        logger.error("[%s] Booking rejected, missing fields: %s", tenant.slug, missing)
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

    dt = parse_datetime(data.preferred_datetime, tz=tenant.timezone)
    confirmed = humanize_datetime(dt, fallback=data.preferred_datetime)
    reference = generate_booking_reference(prefix=tenant.booking_reference_prefix)
    call_id = (call or {}).get("call_id", "")
    extra_fields = compute_extra_fields(args)

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds") + "Z",
        "booking_reference": reference,
        "customer_name": data.patient_name,
        "phone_number": data.phone_number,
        "email": data.patient_email,
        "service": data.service,
        "preferred_datetime": data.preferred_datetime,
        "confirmed_datetime": confirmed,
        "notes": data.notes,
        "call_id": call_id,
        "status": "confirmed",
        "extra_fields": extra_fields,
    }

    # 1) Persist to the database — this is the source of truth. If it fails,
    #    the booking fails.
    booking = save_booking(
        db,
        tenant,
        booking_reference=reference,
        service_name=data.service,
        customer_name=data.patient_name,
        phone_number=data.phone_number,
        email=data.patient_email,
        preferred_datetime_raw=data.preferred_datetime,
        confirmed_datetime=confirmed,
        notes=data.notes,
        call_id=call_id,
        extra_fields=extra_fields,
    )
    if booking is None:
        return BookingResponse(
            status="failed",
            message="We couldn't save the booking to our system.",
        )

    # 2) Best-effort notifications (never block a successful booking). The
    #    notifiers catch their own errors, but we wrap them here too so an
    #    unexpected exception can't undo a booking that's already persisted.
    for notify in (
        lambda r: append_booking(r, tenant),
        lambda r: send_confirmation_email(r, tenant),
        lambda r: fire_booking_webhook(r, tenant),
    ):
        try:
            notify(record)
        except Exception as exc:  # noqa: BLE001
            logger.error("[%s] Notification failed: %s", tenant.slug, exc)

    logger.info("[%s] Booking confirmed: %s for %s", tenant.slug, reference, data.patient_name)
    return BookingResponse(
        status="success",
        booking_reference=reference,
        confirmed_datetime=confirmed,
        message="Booking confirmed.",
    )


@app.post("/webhook/{tenant_slug}/retell-events")
async def retell_events(
    tenant_slug: str, request: Request, db: Session = Depends(get_db)
) -> dict:
    """Optional: log agent-level call lifecycle events (started/ended/analyzed).

    Configure this URL as the agent Webhook in the Retell dashboard. Signature
    verification can be added with the Retell SDK's Retell.verify() helper.
    """
    tenant = get_tenant_or_404(db, tenant_slug)
    try:
        body = await request.json()
    except Exception:  # noqa: BLE001
        body = {}
    event = body.get("event", "unknown")
    call_id = (body.get("call") or {}).get("call_id", "")
    logger.info("[%s] Retell event '%s' for call %s", tenant.slug, event, call_id)
    # Persist the call so the business-owner portal can show a call log +
    # analytics. Best-effort: record_call_event swallows its own errors.
    record_call_event(db, tenant, body)
    return {"received": True}


# --------------------------------------------------------------------------- #
# Frontend static serving (production build) -- must stay last so it never
# shadows /health, /webhook/*, or /api/* routes registered above.
# --------------------------------------------------------------------------- #
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend" / "dist"

if FRONTEND_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="frontend-assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str) -> FileResponse:
        candidate = (FRONTEND_DIR / full_path).resolve()
        if full_path and candidate.is_file() and FRONTEND_DIR.resolve() in candidate.parents:
            return FileResponse(candidate)
        return FileResponse(FRONTEND_DIR / "index.html")
