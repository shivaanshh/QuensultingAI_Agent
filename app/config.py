"""Application configuration, loaded from environment variables.

All secrets and deployment-specific values live here so nothing sensitive is
hard-coded. Values are read once at import time.
"""
from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()  # read a local .env file in development; no-op in production


class Settings:
    # --- Clinic ---
    CLINIC_NAME: str = os.getenv("CLINIC_NAME", "QuensultingAI Dental Clinic")
    CLINIC_TIMEZONE: str = os.getenv("CLINIC_TIMEZONE", "Asia/Kolkata")
    # Working hours (24h). Monday=0 ... Sunday=6. Open Mon-Sat.
    OPEN_HOUR: int = int(os.getenv("OPEN_HOUR", "9"))
    CLOSE_HOUR: int = int(os.getenv("CLOSE_HOUR", "18"))
    OPEN_WEEKDAYS: tuple[int, ...] = (0, 1, 2, 3, 4, 5)  # Mon-Sat

    # --- Shared secret to protect the webhook endpoints ---
    # Retell custom-tool calls append this as a query param (?token=...).
    WEBHOOK_SECRET: str = os.getenv("WEBHOOK_SECRET", "")

    # --- Google Sheets ---
    GOOGLE_SHEETS_ID: str = os.getenv("GOOGLE_SHEETS_ID", "")
    # Two ways to supply the service-account key:
    #   1. GOOGLE_CREDENTIALS_FILE — a path to the JSON key on disk (local dev).
    #   2. GOOGLE_CREDENTIALS_JSON — the raw JSON string (cloud hosts where you
    #      can't upload a file; paste the whole key into one env var).
    GOOGLE_CREDENTIALS_FILE: str = os.getenv(
        "GOOGLE_CREDENTIALS_FILE", "google-credentials.json"
    )
    GOOGLE_CREDENTIALS_JSON: str = os.getenv("GOOGLE_CREDENTIALS_JSON", "")
    BOOKINGS_WORKSHEET: str = os.getenv("BOOKINGS_WORKSHEET", "Bookings")

    # --- Email (SMTP) ---
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    FROM_EMAIL: str = os.getenv("FROM_EMAIL", os.getenv("SMTP_USER", ""))
    # Front-desk inbox that gets a copy of every booking.
    CLINIC_INBOX: str = os.getenv("CLINIC_INBOX", "")

    # --- Optional outbound webhook (satisfies "email OR webhook") ---
    # If set, every successful booking is also POSTed here (e.g. n8n / Zapier).
    BOOKING_WEBHOOK_URL: str = os.getenv("BOOKING_WEBHOOK_URL", "")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
