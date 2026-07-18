"""Business-owner portal HTTP API: the read + management surface behind the
`frontend/` client portal (call log, analytics, and CRUD for bookings /
services / settings).

Same no-auth posture as app.admin_api (a deliberate, explicit product
decision for this iteration) -- responses never include `webhook_secret`,
and nothing here is linked from public marketing pages. Routes are additive
to the same `/api` surface; this module is split out only to keep the
tenant-facing read/write endpoints separate from tenant *provisioning*.
"""
from __future__ import annotations

import logging
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette.responses import Response

from .admin_schemas import (
    AnalyticsOut,
    BookingOut,
    BookingStatusUpdate,
    CallEventOut,
    LabelCount,
    SeriesPoint,
    ServiceCreate,
    ServiceOut,
    ServiceUpdate,
    TenantDetail,
    TenantSettingsUpdate,
)
from .db import get_db
from .db_models import Booking, CallEvent, Service, Tenant

logger = logging.getLogger("agent.portal_api")

router = APIRouter(prefix="/api")


def _tenant(db: Session, slug: str) -> Tenant:
    tenant = db.query(Tenant).filter(Tenant.slug == slug).first()
    if tenant is None:
        raise HTTPException(status_code=404, detail="Unknown tenant")
    return tenant


def _tenant_detail(tenant: Tenant) -> Tenant:
    """Shape a Tenant for the TenantDetail response (recent bookings only)."""
    tenant.bookings = sorted(tenant.bookings, key=lambda b: b.created_at, reverse=True)[:25]
    return tenant


# --------------------------------------------------------------------------- #
# Call log
# --------------------------------------------------------------------------- #
@router.get("/tenants/{slug}/calls", response_model=list[CallEventOut])
def list_calls(slug: str, limit: int = 50, db: Session = Depends(get_db)) -> list[CallEvent]:
    tenant = _tenant(db, slug)
    limit = max(1, min(limit, 200))
    return (
        db.query(CallEvent)
        .filter(CallEvent.tenant_id == tenant.id)
        .order_by(CallEvent.created_at.desc())
        .limit(limit)
        .all()
    )


# --------------------------------------------------------------------------- #
# Analytics
# --------------------------------------------------------------------------- #
@router.get("/tenants/{slug}/analytics", response_model=AnalyticsOut)
def analytics(slug: str, days: int = 30, db: Session = Depends(get_db)) -> AnalyticsOut:
    tenant = _tenant(db, slug)
    days = max(7, min(days, 90))
    today = datetime.now(timezone.utc).date()
    start = today - timedelta(days=days - 1)
    start_iso = start.isoformat()  # 'YYYY-MM-DD' -- ISO8601 timestamps sort lexically after this

    calls = (
        db.query(CallEvent)
        .filter(CallEvent.tenant_id == tenant.id, CallEvent.created_at >= start_iso)
        .all()
    )
    bookings = (
        db.query(Booking)
        .filter(Booking.tenant_id == tenant.id, Booking.created_at >= start_iso)
        .all()
    )

    calls_by_day: dict[str, int] = defaultdict(int)
    bookings_by_day: dict[str, int] = defaultdict(int)
    for c in calls:
        calls_by_day[(c.created_at or "")[:10]] += 1
    for b in bookings:
        bookings_by_day[(b.created_at or "")[:10]] += 1

    series = [
        SeriesPoint(
            date=(d := (start + timedelta(days=i)).isoformat()),
            calls=calls_by_day.get(d, 0),
            bookings=bookings_by_day.get(d, 0),
        )
        for i in range(days)
    ]

    durations = [c.duration_seconds for c in calls if c.duration_seconds]
    total_seconds = sum(durations)
    answered = sum(1 for c in calls if c.call_status in ("ended", "analyzed"))

    sentiment_counts = Counter((c.user_sentiment or "Unknown") for c in calls)
    sentiment = [LabelCount(label=k, count=v) for k, v in sentiment_counts.most_common()]

    service_counts = Counter(b.service_name_snapshot for b in bookings if b.service_name_snapshot)
    top_services = [LabelCount(label=k, count=v) for k, v in service_counts.most_common(6)]

    total_calls = len(calls)
    total_bookings = len(bookings)
    return AnalyticsOut(
        days=days,
        total_calls=total_calls,
        total_bookings=total_bookings,
        total_call_minutes=round(total_seconds / 60, 1),
        avg_call_seconds=int(round(total_seconds / len(durations))) if durations else 0,
        answered_calls=answered,
        booking_conversion=round(total_bookings / total_calls, 3) if total_calls else 0.0,
        provisioned=bool(tenant.retell_agent_id),
        series=series,
        sentiment=sentiment,
        top_services=top_services,
    )


# --------------------------------------------------------------------------- #
# Bookings
# --------------------------------------------------------------------------- #
@router.patch("/tenants/{slug}/bookings/{booking_id}", response_model=BookingOut)
def update_booking_status(
    slug: str, booking_id: int, body: BookingStatusUpdate, db: Session = Depends(get_db)
) -> Booking:
    tenant = _tenant(db, slug)
    booking = (
        db.query(Booking)
        .filter(Booking.tenant_id == tenant.id, Booking.id == booking_id)
        .first()
    )
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    booking.status = body.status
    db.commit()
    db.refresh(booking)
    return booking


# --------------------------------------------------------------------------- #
# Services CRUD
# --------------------------------------------------------------------------- #
@router.get("/tenants/{slug}/services", response_model=list[ServiceOut])
def list_services(slug: str, db: Session = Depends(get_db)) -> list[Service]:
    tenant = _tenant(db, slug)
    return sorted(tenant.services, key=lambda s: (s.sort_order, s.name))


@router.post("/tenants/{slug}/services", response_model=ServiceOut, status_code=201)
def add_service(slug: str, body: ServiceCreate, db: Session = Depends(get_db)) -> Service:
    tenant = _tenant(db, slug)
    next_order = 1 + max((s.sort_order for s in tenant.services), default=0)
    service = Service(
        tenant_id=tenant.id,
        name=body.name.strip(),
        price_display=body.price_display.strip(),
        duration_minutes=body.duration_minutes,
        description=body.description.strip(),
        sort_order=next_order,
        is_active=True,
    )
    db.add(service)
    db.commit()
    db.refresh(service)
    return service


@router.patch("/tenants/{slug}/services/{service_id}", response_model=ServiceOut)
def update_service(
    slug: str, service_id: int, body: ServiceUpdate, db: Session = Depends(get_db)
) -> Service:
    tenant = _tenant(db, slug)
    service = (
        db.query(Service)
        .filter(Service.tenant_id == tenant.id, Service.id == service_id)
        .first()
    )
    if service is None:
        raise HTTPException(status_code=404, detail="Service not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(service, field, value)
    db.commit()
    db.refresh(service)
    return service


@router.delete("/tenants/{slug}/services/{service_id}")
def delete_service(slug: str, service_id: int, db: Session = Depends(get_db)) -> Response:
    tenant = _tenant(db, slug)
    service = (
        db.query(Service)
        .filter(Service.tenant_id == tenant.id, Service.id == service_id)
        .first()
    )
    if service is None:
        raise HTTPException(status_code=404, detail="Service not found")
    db.delete(service)
    db.commit()
    return Response(status_code=204)


# --------------------------------------------------------------------------- #
# Settings
# --------------------------------------------------------------------------- #
@router.patch("/tenants/{slug}/settings", response_model=TenantDetail)
def update_settings(slug: str, body: TenantSettingsUpdate, db: Session = Depends(get_db)) -> Tenant:
    tenant = _tenant(db, slug)
    data = body.model_dump(exclude_unset=True)

    if "open_weekdays" in data:
        wd = data["open_weekdays"]
        if not wd or any((not isinstance(d, int)) or d < 0 or d > 6 for d in wd):
            raise HTTPException(status_code=422, detail="open_weekdays must be a non-empty list of 0-6.")
        data["open_weekdays"] = sorted(set(wd))

    open_hour = data.get("open_hour", tenant.open_hour)
    close_hour = data.get("close_hour", tenant.close_hour)
    if close_hour <= open_hour:
        raise HTTPException(status_code=422, detail="Closing hour must be after opening hour.")

    for field, value in data.items():
        setattr(tenant, field, value)
    db.commit()
    db.refresh(tenant)
    return _tenant_detail(tenant)
