"""Pydantic request/response models for the admin HTTP API (app/admin_api.py).

Kept separate from app/models.py (which describes the RetellAI webhook
payloads) since these describe an unrelated contract -- the admin
dashboard's own read/write shapes.
"""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class ServiceDefaultOut(BaseModel):
    name: str
    price_display: str = ""
    duration_minutes: Optional[int] = None


class CategoryOut(BaseModel):
    key: str
    display_name: str
    agent_persona_name: str
    booking_noun: str
    customer_noun: str
    default_services: list[ServiceDefaultOut]
    fact_bullet_labels: list[tuple[str, str]]
    extra_slots: list[dict]


class ServiceOut(BaseModel):
    id: int
    name: str
    price_display: str
    duration_minutes: Optional[int]
    sort_order: int
    is_active: bool

    model_config = {"from_attributes": True}


class BookingOut(BaseModel):
    id: int
    booking_reference: str
    service_name_snapshot: str
    customer_name: str
    phone_number: str
    email: str
    confirmed_datetime: str
    status: str
    created_at: str
    extra_fields: dict

    model_config = {"from_attributes": True}


class TenantListItem(BaseModel):
    id: int
    slug: str
    category: str
    business_name: str
    status: str
    created_at: str
    provisioned: bool


class TenantDetail(BaseModel):
    id: int
    slug: str
    category: str
    business_name: str
    timezone: str
    open_hour: int
    close_hour: int
    open_weekdays: list[int]
    address: str
    transfer_number: str
    booking_reference_prefix: str
    notification_email: str
    google_sheets_id: str
    retell_voice_id: str
    retell_conversation_flow_id: str
    retell_agent_id: str
    status: str
    created_at: str
    services: list[ServiceOut]
    bookings: list[BookingOut]


class TenantCreateRequest(BaseModel):
    slug: str
    category: str
    business_name: str
    timezone: str = "Asia/Kolkata"
    open_hour: int = 9
    close_hour: int = 18
    open_weekdays: list[int] = Field(default_factory=lambda: [0, 1, 2, 3, 4, 5])
    address: str = ""
    transfer_number: str = ""
    booking_reference_prefix: Optional[str] = None
    notification_email: str = ""
    google_sheets_id: str = ""
    services: list[str] = Field(default_factory=list)


class ProvisionResult(BaseModel):
    conversation_flow_id: str
    agent_id: str


class ContactRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    email: str = Field(..., min_length=3, max_length=200)
    business_type: str = ""
    message: str = Field(..., min_length=1, max_length=4000)


class ContactResponse(BaseModel):
    status: str
    message: str


# --------------------------------------------------------------------------- #
# Business-owner portal: call log, analytics, and management writes.
# --------------------------------------------------------------------------- #
class CallEventOut(BaseModel):
    id: int
    call_id: str
    direction: str
    from_number: str
    to_number: str
    call_status: str
    duration_seconds: Optional[int]
    disconnection_reason: str
    user_sentiment: str
    call_successful: Optional[bool]
    summary: str
    transcript: str
    booking_reference: str
    started_at: Optional[str]
    ended_at: Optional[str]
    created_at: str

    model_config = {"from_attributes": True}


class SeriesPoint(BaseModel):
    date: str          # YYYY-MM-DD
    calls: int
    bookings: int


class LabelCount(BaseModel):
    label: str
    count: int


class AnalyticsOut(BaseModel):
    days: int
    total_calls: int
    total_bookings: int
    total_call_minutes: float
    avg_call_seconds: int
    answered_calls: int
    booking_conversion: float      # bookings / calls, 0..1
    provisioned: bool
    series: list[SeriesPoint]
    sentiment: list[LabelCount]
    top_services: list[LabelCount]


class BookingStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(confirmed|completed|cancelled|no_show)$")


class ServiceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    price_display: str = Field("", max_length=64)
    duration_minutes: Optional[int] = Field(None, ge=0, le=1440)
    description: str = Field("", max_length=2000)


class ServiceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    price_display: Optional[str] = Field(None, max_length=64)
    duration_minutes: Optional[int] = Field(None, ge=0, le=1440)
    description: Optional[str] = Field(None, max_length=2000)
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class TenantSettingsUpdate(BaseModel):
    business_name: Optional[str] = Field(None, min_length=1, max_length=200)
    timezone: Optional[str] = Field(None, max_length=64)
    open_hour: Optional[int] = Field(None, ge=0, le=23)
    close_hour: Optional[int] = Field(None, ge=0, le=23)
    open_weekdays: Optional[list[int]] = None
    address: Optional[str] = Field(None, max_length=2000)
    transfer_number: Optional[str] = Field(None, max_length=32)
    notification_email: Optional[str] = Field(None, max_length=200)
    status: Optional[str] = Field(None, pattern="^(active|paused|draft)$")
