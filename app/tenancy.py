"""Tenant resolution for the multi-tenant backend."""
from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .db_models import Tenant


def get_tenant_or_404(db: Session, tenant_slug: str) -> Tenant:
    tenant = (
        db.query(Tenant)
        .filter(Tenant.slug == tenant_slug, Tenant.status == "active")
        .first()
    )
    if tenant is None:
        raise HTTPException(status_code=404, detail="Unknown tenant")
    return tenant
