"""Pydantic models describing the payloads exchanged with RetellAI.

RetellAI custom tools POST a body shaped like:
    { "call": {...}, "name": "book_appointment", "args": { ... } }

We validate only the `args` we care about and keep the rest permissive, so a
minor change on Retell's side never 500s the endpoint. The per-tenant
service list now lives in the `services` database table (see
app/db_models.py) rather than a hardcoded constant here.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class RetellToolCall(BaseModel):
    """The raw envelope Retell sends for a custom function call."""

    call: Optional[dict] = None
    name: Optional[str] = None
    args: Optional[dict] = None

    model_config = {"extra": "allow"}


class CheckAvailabilityArgs(BaseModel):
    preferred_datetime: str = Field(..., description="Natural-language date/time")
    service: Optional[str] = None


class BookAppointmentArgs(BaseModel):
    patient_name: str
    phone_number: str
    service: str
    preferred_datetime: str
    patient_email: Optional[str] = ""
    notes: Optional[str] = ""


class AvailabilityResponse(BaseModel):
    # Returned as strings so Retell equation edges (== "true") match reliably.
    available: str
    reason: str
    suggested_slots: str = ""


class BookingResponse(BaseModel):
    status: str  # "success" | "failed"
    booking_reference: str = ""
    confirmed_datetime: str = ""
    message: str = ""
