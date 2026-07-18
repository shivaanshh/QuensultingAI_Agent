"""Shared test fixtures.

The suite runs against an in-memory SQLite database (shared across the whole
session via StaticPool) instead of the real DATABASE_URL, so tests never
touch developer/production data. A single "quensulting-dental" tenant is
seeded once so the tenant-scoped webhook tests have something to resolve.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import db, db_models

TENANT_SLUG = "quensulting-dental"

_test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(bind=_test_engine, autoflush=False, autocommit=False)


@pytest.fixture(scope="session", autouse=True)
def _setup_test_db():
    db.Base.metadata.create_all(bind=_test_engine)
    session = TestSessionLocal()
    try:
        session.add(
            db_models.Tenant(
                slug=TENANT_SLUG,
                category="dental_medical",
                business_name="QuensultingAI Dental Clinic",
                timezone="Asia/Kolkata",
                open_hour=9,
                close_hour=18,
                open_weekdays=[0, 1, 2, 3, 4, 5],
                address="3rd Floor, Baner Business Hub, Baner Road, Pune 411045",
                webhook_secret="",
                booking_reference_prefix="QDC",
            )
        )
        session.commit()
    finally:
        session.close()
    yield
    db.Base.metadata.drop_all(bind=_test_engine)


@pytest.fixture(autouse=True)
def _override_get_db():
    from app.main import app

    def _get_test_db():
        session = TestSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[db.get_db] = _get_test_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def db_session():
    """A fresh session onto the shared in-memory test DB, for tests that
    need to read/mutate a tenant row directly (e.g. the token guard test)."""
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()
