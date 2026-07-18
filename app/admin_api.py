"""Admin HTTP API: tenant management for the marketing site + admin
dashboard frontend (frontend/).

No authentication in this iteration (a deliberate, explicit product
decision) -- so responses here must never include `webhook_secret`, and
this router should not be linked from public marketing pages or exposed
on a memorable custom domain until real auth exists.

Every route is a thin wrapper around functions that already exist and are
already used by scripts/create_tenant.py: app.onboarding.create_tenant_row,
app.flow_builder.build_flow/validate_flow, app.provisioning.provision_tenant.
Nothing here reimplements that logic.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .admin_schemas import (
    CategoryOut,
    ContactRequest,
    ContactResponse,
    ProvisionResult,
    TenantCreateRequest,
    TenantDetail,
    TenantListItem,
)
from .config import settings
from .db import get_db
from .db_models import Tenant
from .flow_builder import build_flow, validate_flow
from .notifications import send_contact_notification
from .onboarding import TenantValidationError, create_tenant_row
from .provisioning import ProvisioningError, provision_tenant
from .templates.registry import CATEGORY_TEMPLATES, get_template

logger = logging.getLogger("agent.admin_api")

router = APIRouter(prefix="/api")


def _get_tenant_any_status(db: Session, slug: str) -> Tenant:
    """Admin lookup: unlike tenancy.get_tenant_or_404, this does NOT filter
    by status -- admins must be able to view paused/draft tenants too."""
    tenant = db.query(Tenant).filter(Tenant.slug == slug).first()
    if tenant is None:
        raise HTTPException(status_code=404, detail="Unknown tenant")
    return tenant


@router.get("/categories", response_model=list[CategoryOut])
def list_categories() -> list[CategoryOut]:
    return [
        CategoryOut(
            key=t.key,
            display_name=t.display_name,
            agent_persona_name=t.agent_persona_name,
            booking_noun=t.booking_noun,
            customer_noun=t.customer_noun,
            default_services=[
                {"name": s.name, "price_display": s.price_display, "duration_minutes": s.duration_minutes}
                for s in t.default_services
            ],
            fact_bullet_labels=list(t.fact_bullet_labels),
            extra_slots=list(t.extra_slots),
        )
        for t in sorted(CATEGORY_TEMPLATES.values(), key=lambda t: t.display_name)
    ]


@router.get("/tenants", response_model=list[TenantListItem])
def list_tenants(db: Session = Depends(get_db)) -> list[TenantListItem]:
    tenants = db.query(Tenant).order_by(Tenant.created_at.desc()).all()
    return [
        TenantListItem(
            id=t.id,
            slug=t.slug,
            category=t.category,
            business_name=t.business_name,
            status=t.status,
            created_at=t.created_at,
            provisioned=bool(t.retell_agent_id),
        )
        for t in tenants
    ]


@router.get("/tenants/{slug}", response_model=TenantDetail)
def get_tenant_detail(slug: str, db: Session = Depends(get_db)) -> Tenant:
    tenant = _get_tenant_any_status(db, slug)
    # Cap recent bookings so a long-lived tenant's payload stays small.
    tenant.bookings = sorted(tenant.bookings, key=lambda b: b.created_at, reverse=True)[:25]
    return tenant


@router.post("/tenants", response_model=TenantDetail, status_code=201)
def create_tenant(body: TenantCreateRequest, db: Session = Depends(get_db)) -> Tenant:
    try:
        tenant = create_tenant_row(
            db,
            slug=body.slug,
            category=body.category,
            business_name=body.business_name,
            timezone=body.timezone,
            open_hour=body.open_hour,
            close_hour=body.close_hour,
            open_weekdays=body.open_weekdays,
            address=body.address,
            transfer_number=body.transfer_number,
            booking_reference_prefix=body.booking_reference_prefix,
            notification_email=body.notification_email,
            google_sheets_id=body.google_sheets_id,
            services=body.services,
        )
    except TenantValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return tenant


@router.get("/tenants/{slug}/preview")
def preview_tenant_flow(slug: str, db: Session = Depends(get_db)) -> dict:
    tenant = _get_tenant_any_status(db, slug)
    template = get_template(tenant.category)
    backend_base_url = settings.BACKEND_BASE_URL or "https://YOUR_BACKEND_URL"
    flow = build_flow(tenant, template, backend_base_url)
    try:
        validate_flow(flow)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return flow


@router.post("/tenants/{slug}/provision", response_model=ProvisionResult)
def provision(slug: str, reprovision: bool = False, db: Session = Depends(get_db)) -> ProvisionResult:
    tenant = _get_tenant_any_status(db, slug)
    if tenant.retell_agent_id and not reprovision:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Tenant '{tenant.slug}' already has an agent "
                f"(retell_agent_id={tenant.retell_agent_id!r}). Pass ?reprovision=true "
                "to create a new, independent agent/flow anyway."
            ),
        )
    if not settings.RETELL_API_KEY:
        raise HTTPException(status_code=503, detail="RETELL_API_KEY is not configured on the server.")
    backend_base_url = settings.BACKEND_BASE_URL
    if not backend_base_url:
        raise HTTPException(status_code=503, detail="BACKEND_BASE_URL is not configured on the server.")

    template = get_template(tenant.category)
    try:
        result = provision_tenant(
            tenant, template, backend_base_url, settings.RETELL_API_KEY, api_base=settings.RETELL_API_BASE
        )
    except ProvisioningError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    tenant.retell_voice_id = template.default_voice_id
    tenant.retell_conversation_flow_id = result["conversation_flow_id"]
    tenant.retell_agent_id = result["agent_id"]
    db.commit()
    return ProvisionResult(**result)


@router.post("/contact", response_model=ContactResponse)
def submit_contact(body: ContactRequest) -> ContactResponse:
    if "@" not in body.email or "." not in body.email.split("@")[-1]:
        raise HTTPException(status_code=422, detail="Please provide a valid email address.")
    sent = send_contact_notification(body.name, body.email, body.message, business_type=body.business_type)
    if not sent:
        logger.warning("Contact form submission from %s could not be emailed.", body.email)
        return ContactResponse(
            status="received",
            message="Thanks -- we've logged your message. If it's urgent, please email us directly.",
        )
    return ContactResponse(status="sent", message="Thanks for reaching out -- we'll be in touch shortly.")
