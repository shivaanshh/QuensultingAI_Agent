"""One-time migration: insert the live QuensultingAI Dental Clinic as tenant #1.

This hand-inserts the facts that were previously hardcoded across
app/config.py and retell_conversation_flow.json, so the existing live Retell
agent can be pointed at the new tenant-scoped webhook paths
(/webhook/quensulting-dental/...) without any behavior change.

Idempotent: re-running updates the existing row (matched by slug) instead of
creating a duplicate, so it's safe to re-run after editing the facts below.

Usage:
    python scripts/seed_dental_tenant.py
    python scripts/seed_dental_tenant.py --retell-agent-id agent_xxx --retell-flow-id conversation_flow_xxx
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db import Base, SessionLocal, engine  # noqa: E402
from app.db_models import Service, Tenant  # noqa: E402

TENANT_SLUG = "quensulting-dental"

# Real clinic facts, transcribed from .env and the global_prompt in
# retell_conversation_flow.json (the live-tested, hand-built agent).
TENANT_FACTS = dict(
    slug=TENANT_SLUG,
    category="dental_medical",
    business_name="QuensultingAI Dental Clinic",
    timezone="Asia/Kolkata",
    open_hour=9,
    close_hour=18,
    open_weekdays=[0, 1, 2, 3, 4, 5],  # Monday-Saturday
    address="3rd Floor, Baner Business Hub, Baner Road, Pune 411045",
    # Placeholder from the original flow's default_dynamic_variables --
    # replace with the clinic's real front-desk transfer number.
    transfer_number="+919000000000",
    # Reused from the existing .env so the live agent's ?token=... doesn't
    # need to change when its tool URLs are updated.
    webhook_secret="mcfecMGZXQ4wCtYrtGVg9SXNlTQuv6TN",
    booking_reference_prefix="QDC",
    notification_email="eternalmemories4all@gmail.com",
    booking_webhook_url="",
    google_sheets_id="1pTx7dfacDm8yPRkSvnb5LQF4jp6lEYK3PCr-cmJKKSA",
    extra_facts={
        "consultation_fee": "500 rupees, adjusted against treatment cost if the patient proceeds same day",
        "walk_ins": "Accepted, but appointments are strongly preferred to avoid waiting",
        "emergency_slots": "Same-day emergency slots available during working hours whenever possible",
        "payment_methods": "Cash, UPI, credit and debit cards; most major dental insurance plans accepted",
    },
    status="active",
)

# Names transcribed verbatim from the global_prompt's services list. Only the
# consultation fee was ever spoken as a real price -- the rest have no
# published price in the source material, so price_display is left blank
# rather than inventing a number.
SERVICES = [
    dict(name="Dental Cleaning", sort_order=0),
    dict(name="Root Canal Treatment", sort_order=1),
    dict(name="Teeth Whitening", sort_order=2),
    dict(name="Braces Consultation", sort_order=3),
    dict(name="Tooth Extraction", sort_order=4),
    dict(name="General Dental Consultation", price_display="₹500", sort_order=5),
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--retell-voice-id", default="", help="Existing live agent's voice_id")
    parser.add_argument("--retell-flow-id", default="", help="Existing live agent's conversation_flow_id")
    parser.add_argument("--retell-agent-id", default="", help="Existing live agent's agent_id")
    args = parser.parse_args()

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        tenant = db.query(Tenant).filter_by(slug=TENANT_SLUG).first()
        facts = dict(TENANT_FACTS)
        facts["retell_voice_id"] = args.retell_voice_id
        facts["retell_conversation_flow_id"] = args.retell_flow_id
        facts["retell_agent_id"] = args.retell_agent_id

        if tenant is None:
            tenant = Tenant(**facts)
            db.add(tenant)
            print(f"Creating tenant '{TENANT_SLUG}'...")
        else:
            for key, value in facts.items():
                setattr(tenant, key, value)
            print(f"Updating existing tenant '{TENANT_SLUG}'...")
        db.commit()
        db.refresh(tenant)

        existing_names = {s.name for s in tenant.services}
        for svc in SERVICES:
            if svc["name"] not in existing_names:
                db.add(Service(tenant_id=tenant.id, **svc))
        db.commit()

        print(f"Tenant id={tenant.id} slug={tenant.slug!r} ready with {len(tenant.services)} services.")
        print(f"Webhook base: /webhook/{tenant.slug}/...")
        print(f"Token: ?token={tenant.webhook_secret}")
        if not args.retell_agent_id:
            print(
                "\nNOTE: retell_agent_id / retell_conversation_flow_id / retell_voice_id were "
                "left blank. Fill them in with --retell-agent-id / --retell-flow-id / "
                "--retell-voice-id (or edit the row directly) once you've noted them from the "
                "Retell dashboard -- they're for your own reference and aren't read by the API."
            )
        print(
            "\nNext manual step: in the Retell dashboard, update this agent's two custom-tool "
            f"URLs to https://<your-backend>/webhook/{tenant.slug}/check-availability and "
            f".../book-appointment (append ?token={tenant.webhook_secret} to each)."
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
