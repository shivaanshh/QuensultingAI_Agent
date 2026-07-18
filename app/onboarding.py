"""Shared tenant-creation validation and insertion logic.

Used by both scripts/create_tenant.py (CLI) and app/admin_api.py (HTTP), so
a slug/category/hours rule only needs to be written once. validate_tenant_input
does pure checks plus a uniqueness query and never writes; create_tenant_row
calls it, then inserts. Kept as two layers because the CLI's --dry-run path
needs to validate without ever touching the database.
"""
from __future__ import annotations

import re
import secrets
from typing import Optional, Sequence

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .db_models import Service, Tenant
from .templates.registry import CATEGORY_TEMPLATES

_SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


class TenantValidationError(ValueError):
    """Invalid tenant-creation input, or a slug that's already taken."""


def validate_tenant_input(
    db: Session,
    *,
    slug: str,
    category: str,
    business_name: str,
    open_hour: int,
    close_hour: int,
    open_weekdays: Sequence[int],
) -> None:
    if not slug or not _SLUG_RE.match(slug):
        raise TenantValidationError(
            f"slug {slug!r} is invalid -- use lowercase letters, digits, and hyphens only "
            "(e.g. 'glow-salon'), since it becomes part of the webhook URL path."
        )
    if category not in CATEGORY_TEMPLATES:
        raise TenantValidationError(
            f"category {category!r} is not a known category. "
            f"Choose one of: {', '.join(sorted(CATEGORY_TEMPLATES))}."
        )
    if not business_name or not business_name.strip():
        raise TenantValidationError("business_name is required.")
    if open_hour < 0 or open_hour > 23 or close_hour < 0 or close_hour > 23:
        raise TenantValidationError("open_hour/close_hour must be between 0 and 23.")
    if close_hour <= open_hour:
        raise TenantValidationError(f"close_hour ({close_hour}) must be after open_hour ({open_hour}).")
    if not open_weekdays or any(d < 0 or d > 6 for d in open_weekdays):
        raise TenantValidationError("open_weekdays values must be between 0 (Monday) and 6 (Sunday).")
    if db.query(Tenant).filter_by(slug=slug).first() is not None:
        raise TenantValidationError(f"Tenant '{slug}' already exists.")


def create_tenant_row(
    db: Session,
    *,
    slug: str,
    category: str,
    business_name: str,
    timezone: str = "Asia/Kolkata",
    open_hour: int = 9,
    close_hour: int = 18,
    open_weekdays: Sequence[int] = (0, 1, 2, 3, 4, 5),
    address: str = "",
    transfer_number: str = "",
    booking_reference_prefix: Optional[str] = None,
    notification_email: str = "",
    google_sheets_id: str = "",
    services: Optional[Sequence[str]] = None,
) -> Tenant:
    """Validate and insert a new tenant row (+ starter services). Raises
    TenantValidationError on invalid input or a duplicate slug."""
    validate_tenant_input(
        db,
        slug=slug,
        category=category,
        business_name=business_name,
        open_hour=open_hour,
        close_hour=close_hour,
        open_weekdays=open_weekdays,
    )
    tenant = Tenant(
        slug=slug,
        category=category,
        business_name=business_name,
        timezone=timezone,
        open_hour=open_hour,
        close_hour=close_hour,
        open_weekdays=list(open_weekdays),
        address=address,
        transfer_number=transfer_number,
        webhook_secret=secrets.token_urlsafe(24),
        booking_reference_prefix=(booking_reference_prefix or slug[:3].upper()),
        notification_email=notification_email,
        google_sheets_id=google_sheets_id,
    )
    tenant.services = [
        Service(name=name, sort_order=i, is_active=True)
        for i, name in enumerate(services or [])
    ]
    db.add(tenant)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise TenantValidationError(f"Tenant '{slug}' already exists.") from None
    db.refresh(tenant)
    return tenant
