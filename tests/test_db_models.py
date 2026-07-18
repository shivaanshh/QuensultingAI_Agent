"""CRUD round-trip tests for the Tenant/Service/Booking ORM models, on the
shared in-memory test DB from tests/conftest.py.
"""
import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from app.db_models import Booking, Service, Tenant


def _unique_slug(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def test_tenant_service_booking_round_trip(db_session):
    tenant = Tenant(
        slug=_unique_slug("crud-tenant"),
        category="dental_medical",
        business_name="CRUD Test Clinic",
        timezone="Asia/Kolkata",
        open_hour=9,
        close_hour=18,
        open_weekdays=[0, 1, 2, 3, 4, 5],
        address="42 Test Ave",
        webhook_secret="secret",
        booking_reference_prefix="CRT",
        extra_facts={"walk_ins": "Accepted"},
    )
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)

    assert tenant.id is not None
    assert tenant.open_weekdays == [0, 1, 2, 3, 4, 5]
    assert tenant.extra_facts == {"walk_ins": "Accepted"}
    assert tenant.status == "active"

    service = Service(tenant_id=tenant.id, name="Dental Cleaning", price_display="₹500", sort_order=0)
    db_session.add(service)
    db_session.commit()
    db_session.refresh(service)

    assert service.is_active is True

    booking = Booking(
        tenant_id=tenant.id,
        booking_reference="CRT-0001",
        service_name_snapshot="Dental Cleaning",
        customer_name="Priya Sharma",
        phone_number="+919812345678",
        preferred_datetime_raw="next Monday at 3pm",
        confirmed_datetime="2026-07-20T15:00:00+05:30",
        extra_fields={"party_size": 2},
    )
    db_session.add(booking)
    db_session.commit()
    db_session.refresh(booking)

    assert booking.id is not None
    assert booking.extra_fields == {"party_size": 2}
    assert booking.status == "confirmed"

    db_session.refresh(tenant)
    assert len(tenant.services) == 1
    assert tenant.services[0].name == "Dental Cleaning"
    assert len(tenant.bookings) == 1
    assert tenant.bookings[0].booking_reference == "CRT-0001"


def test_booking_reference_unique_per_tenant(db_session):
    tenant = Tenant(
        slug=_unique_slug("crud-tenant-dupe"),
        category="dental_medical",
        business_name="Dupe Test Clinic",
        webhook_secret="secret",
        booking_reference_prefix="DUP",
    )
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)

    db_session.add(Booking(
        tenant_id=tenant.id,
        booking_reference="DUP-0001",
        service_name_snapshot="Dental Cleaning",
        customer_name="A",
        phone_number="1",
        preferred_datetime_raw="today",
        confirmed_datetime="2026-07-20T15:00:00+05:30",
    ))
    db_session.commit()

    db_session.add(Booking(
        tenant_id=tenant.id,
        booking_reference="DUP-0001",
        service_name_snapshot="Dental Cleaning",
        customer_name="B",
        phone_number="2",
        preferred_datetime_raw="tomorrow",
        confirmed_datetime="2026-07-21T15:00:00+05:30",
    ))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_tenant_slug_unique(db_session):
    slug = _unique_slug("crud-tenant-slugdupe")
    db_session.add(Tenant(slug=slug, category="dental_medical", business_name="A", webhook_secret="s1"))
    db_session.commit()

    db_session.add(Tenant(slug=slug, category="dental_medical", business_name="B", webhook_secret="s2"))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_deleting_tenant_cascades_to_services_and_bookings(db_session):
    tenant = Tenant(
        slug=_unique_slug("crud-tenant-cascade"),
        category="dental_medical",
        business_name="Cascade Test Clinic",
        webhook_secret="secret",
    )
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)

    db_session.add(Service(tenant_id=tenant.id, name="X", sort_order=0))
    db_session.add(Booking(
        tenant_id=tenant.id,
        booking_reference="CAS-0001",
        service_name_snapshot="X",
        customer_name="A",
        phone_number="1",
        preferred_datetime_raw="today",
        confirmed_datetime="2026-07-20T15:00:00+05:30",
    ))
    db_session.commit()

    tenant_id = tenant.id
    db_session.delete(tenant)
    db_session.commit()

    assert db_session.query(Service).filter_by(tenant_id=tenant_id).count() == 0
    assert db_session.query(Booking).filter_by(tenant_id=tenant_id).count() == 0
