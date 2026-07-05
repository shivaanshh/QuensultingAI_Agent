"""Shared test fixtures.

The suite must pass regardless of what's in the developer's real .env — most
tests call the webhooks with no token, so WEBHOOK_SECRET must default to "" in
tests even if a real secret is configured for local/prod use. Individual tests
(e.g. test_token_required) can still monkeypatch it back on.
"""
import pytest

from app.config import settings


@pytest.fixture(autouse=True)
def _reset_webhook_secret(monkeypatch):
    monkeypatch.setattr(settings, "WEBHOOK_SECRET", "")
