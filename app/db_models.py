"""SQLAlchemy ORM models: Tenant, Service, Booking.

Datetimes are stored as ISO8601 text, not a SQLAlchemy DateTime column --
SQLite has no real tz-aware datetime type, and silently dropping tzinfo on
round-trip would reintroduce the kind of parsing bug already fixed once in
app/utils.py (see parse_datetime's word-number and next-weekday fixes).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    business_name: Mapped[str] = mapped_column(String(200), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="Asia/Kolkata")
    open_hour: Mapped[int] = mapped_column(Integer, nullable=False, default=9)
    close_hour: Mapped[int] = mapped_column(Integer, nullable=False, default=18)
    # JSON list of ints, Monday=0 ... Sunday=6.
    open_weekdays: Mapped[list] = mapped_column(JSON, nullable=False, default=lambda: [0, 1, 2, 3, 4, 5])
    address: Mapped[str] = mapped_column(Text, nullable=False, default="")
    transfer_number: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    # Per-tenant secret checked against the Retell tool call's ?token=... param.
    webhook_secret: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    booking_reference_prefix: Mapped[str] = mapped_column(String(16), nullable=False, default="BK")
    notification_email: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    booking_webhook_url: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # Optional per-tenant Sheets export; blank means Sheets is skipped entirely.
    google_sheets_id: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    retell_voice_id: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    retell_conversation_flow_id: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    retell_agent_id: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    # Free-form category copy facts (fees, payment methods, policies, ...)
    # consumed only by prompt templating -- never queried in SQL.
    extra_facts: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")
    created_at: Mapped[str] = mapped_column(String(32), nullable=False, default=_now_iso)
    updated_at: Mapped[str] = mapped_column(
        String(32), nullable=False, default=_now_iso, onupdate=_now_iso
    )

    services: Mapped[list["Service"]] = relationship(
        back_populates="tenant", cascade="all, delete-orphan"
    )
    bookings: Mapped[list["Booking"]] = relationship(
        back_populates="tenant", cascade="all, delete-orphan"
    )


class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    # Free-form display text (e.g. "₹500", "Starts at $80") -- the app only
    # ever speaks a price, it never computes totals or charges anything.
    price_display: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    duration_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    tenant: Mapped["Tenant"] = relationship(back_populates="services")


class CallEvent(Base):
    """One row per phone call, upserted as Retell posts lifecycle events
    (call_started -> call_ended -> call_analyzed) to /webhook/{slug}/retell-events.

    This is the substrate for the business-owner portal's call log and
    analytics. Like bookings, timestamps are ISO8601 text (see module docstring).
    Rows only appear once the agent's Webhook URL is configured in Retell and
    real calls come in -- there is no synthetic data.
    """

    __tablename__ = "call_events"
    __table_args__ = (
        UniqueConstraint("tenant_id", "call_id", name="uq_call_per_tenant"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    call_id: Mapped[str] = mapped_column(String(96), nullable=False, index=True)
    direction: Mapped[str] = mapped_column(String(16), nullable=False, default="")
    from_number: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    to_number: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    # ongoing | ended | analyzed  (mirrors how far the lifecycle has progressed)
    call_status: Mapped[str] = mapped_column(String(16), nullable=False, default="ongoing")
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    disconnection_reason: Mapped[str] = mapped_column(String(48), nullable=False, default="")
    # Positive | Neutral | Negative | Unknown, straight from Retell's analysis.
    user_sentiment: Mapped[str] = mapped_column(String(16), nullable=False, default="")
    call_successful: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    transcript: Mapped[str] = mapped_column(Text, nullable=False, default="")
    booking_reference: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    started_at: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    ended_at: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    created_at: Mapped[str] = mapped_column(String(32), nullable=False, default=_now_iso)
    updated_at: Mapped[str] = mapped_column(
        String(32), nullable=False, default=_now_iso, onupdate=_now_iso
    )


class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = (
        UniqueConstraint("tenant_id", "booking_reference", name="uq_booking_ref_per_tenant"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    booking_reference: Mapped[str] = mapped_column(String(32), nullable=False)
    service_name_snapshot: Mapped[str] = mapped_column(String(200), nullable=False)
    customer_name: Mapped[str] = mapped_column(String(200), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(32), nullable=False)
    email: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    preferred_datetime_raw: Mapped[str] = mapped_column(String(200), nullable=False)
    confirmed_datetime: Mapped[str] = mapped_column(String(64), nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # Any category-specific slot beyond the fixed columns above (e.g.
    # party_size, urgency_level, insurance_provider) lands here -- adding a
    # new per-category field never needs a schema migration.
    extra_fields: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    call_id: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="confirmed")
    created_at: Mapped[str] = mapped_column(String(32), nullable=False, default=_now_iso)

    tenant: Mapped["Tenant"] = relationship(back_populates="bookings")
