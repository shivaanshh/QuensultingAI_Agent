"""Platform-level configuration, loaded from environment variables.

Everything business-specific (hours, services, webhook secret, Sheets ID,
etc.) now lives per-tenant in the database (see app/db_models.py) rather
than here. This file only holds settings shared by every tenant: how to
reach the database, the Retell API, and the shared notification transports.
"""
from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()  # read a local .env file in development; no-op in production


class Settings:
    # --- Database ---
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/tenants.db")

    # --- RetellAI provisioning ---
    RETELL_API_KEY: str = os.getenv("RETELL_API_KEY", "")
    RETELL_API_BASE: str = os.getenv("RETELL_API_BASE", "https://api.retellai.com")
    # Public base URL this backend is reachable at (used to build tool webhook
    # URLs when provisioning a new tenant's Retell agent).
    BACKEND_BASE_URL: str = os.getenv("BACKEND_BASE_URL", "")

    # --- Google Sheets (shared service account; each tenant supplies its own
    # spreadsheet ID if it wants a Sheets export) ---
    GOOGLE_CREDENTIALS_FILE: str = os.getenv(
        "GOOGLE_CREDENTIALS_FILE", "google-credentials.json"
    )
    GOOGLE_CREDENTIALS_JSON: str = os.getenv("GOOGLE_CREDENTIALS_JSON", "")
    BOOKINGS_WORKSHEET: str = os.getenv("BOOKINGS_WORKSHEET", "Bookings")

    # --- Email (SMTP) — one shared sending identity for all tenants in v1 ---
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    FROM_EMAIL: str = os.getenv("FROM_EMAIL", os.getenv("SMTP_USER", ""))


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
