"""Seed a clearly-labelled DEMO tenant with realistic sample calls + bookings
so the client portal dashboard demonstrates fully (populated charts, call log,
bookings) without waiting for real traffic.

This is sample/showcase data for a *demo* tenant only -- it never touches the
QuensultingAI dental reference tenant, and the data is obviously illustrative.
Idempotent: re-running clears this demo tenant's calls/bookings and reseeds.

    python scripts/seed_demo_data.py                 # default demo-glow-salon
    python scripts/seed_demo_data.py --slug demo-x --days 30 --calls 55 --bookings 34
"""
from __future__ import annotations

import argparse
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db import SessionLocal, init_db  # noqa: E402
from app.db_models import Booking, CallEvent, Service, Tenant  # noqa: E402
from app.onboarding import create_tenant_row  # noqa: E402

FIRST = ["Priya", "Arjun", "Sana", "Rahul", "Meera", "Vikram", "Ananya", "Karan",
         "Isha", "Rohan", "Neha", "Aditya", "Diya", "Farhan", "Lena", "Omar",
         "Grace", "Marcus", "Chloe", "Diego", "Yuki", "Nadia"]
LAST = ["Sharma", "Patel", "Khan", "Reddy", "Nair", "Gupta", "Singh", "Rao",
        "Chen", "Silva", "Ahmed", "Costa", "Kim", "Oyelaran", "Novak"]

SERVICES = [
    ("Haircut & Styling", "$45"),
    ("Manicure & Pedicure", "$40"),
    ("Hair Colour", "Starts at $80"),
    ("Facial", "$60"),
    ("Full Head Highlights", "$120"),
]

SUMMARIES_BOOKED = [
    "Caller booked a {svc} for {when}. Confirmed by SMS.",
    "New client scheduled a {svc}; asked about parking, answered.",
    "Rebooked a regular for a {svc} next week.",
    "Booked {svc} and added a note about sensitive skin.",
]
SUMMARIES_NOBOOK = [
    "Caller asked about pricing for {svc}; will call back.",
    "Enquiry about opening hours on Sunday. No booking.",
    "Wanted a same-day slot that wasn't available; offered alternatives.",
    "General question about services, no appointment made.",
]

SENTIMENTS = ["Positive"] * 6 + ["Neutral"] * 3 + ["Negative"] * 1
DISCONNECTS = ["user_hangup", "agent_hangup", "call_transfer"]


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds")


def _when_phrase(dt: datetime) -> str:
    return dt.strftime("%a %b %-d at %-I:%M %p") if sys.platform != "win32" else dt.strftime("%a %b %d at %I:%M %p")


def ensure_tenant(db, slug: str) -> Tenant:
    tenant = db.query(Tenant).filter(Tenant.slug == slug).first()
    if tenant is None:
        tenant = create_tenant_row(
            db,
            slug=slug,
            category="salon_spa",
            business_name="Glow Salon & Spa (Demo)",
            timezone="Asia/Kolkata",
            open_hour=10,
            close_hour=20,
            open_weekdays=[0, 1, 2, 3, 4, 5],
            address="12 MG Road, Pune",
            transfer_number="+919000000001",
            notification_email="owner@glowsalon.example",
            booking_reference_prefix="GLW",
            services=[name for name, _ in SERVICES],
        )
    # Give services real prices + mark the demo tenant "live" for the showcase.
    for svc in tenant.services:
        price = dict(SERVICES).get(svc.name)
        if price and not svc.price_display:
            svc.price_display = price
    tenant.status = "active"
    tenant.retell_agent_id = tenant.retell_agent_id or "agent_demo_showcase"
    tenant.retell_conversation_flow_id = tenant.retell_conversation_flow_id or "conversation_flow_demo"
    tenant.retell_voice_id = tenant.retell_voice_id or "11labs-Myra"
    db.commit()
    db.refresh(tenant)
    return tenant


def seed(slug: str, days: int, n_calls: int, n_bookings: int) -> None:
    init_db()
    db = SessionLocal()
    try:
        tenant = ensure_tenant(db, slug)
        service_names = [s.name for s in tenant.services] or [n for n, _ in SERVICES]

        # Idempotent: clear this demo tenant's existing sample data first.
        db.query(CallEvent).filter(CallEvent.tenant_id == tenant.id).delete()
        db.query(Booking).filter(Booking.tenant_id == tenant.id).delete()
        db.commit()

        now = datetime.now(timezone.utc)
        rnd = random.Random(42)  # stable-ish output run to run

        # ── Bookings ──
        made = 0
        for i in range(n_bookings):
            created = now - timedelta(days=rnd.randint(0, days - 1), hours=rnd.randint(0, 10), minutes=rnd.randint(0, 59))
            appt = created + timedelta(days=rnd.randint(1, 12), hours=rnd.randint(0, 6))
            status = rnd.choices(["confirmed", "completed", "cancelled", "no_show"], weights=[5, 4, 2, 1])[0]
            name = f"{rnd.choice(FIRST)} {rnd.choice(LAST)}"
            db.add(Booking(
                tenant_id=tenant.id,
                booking_reference=f"{tenant.booking_reference_prefix}-{1000 + i}",
                service_name_snapshot=rnd.choice(service_names),
                customer_name=name,
                phone_number=f"+9198{rnd.randint(10000000, 99999999)}",
                email="",
                preferred_datetime_raw=_when_phrase(appt),
                confirmed_datetime=_when_phrase(appt),
                notes="",
                status=status,
                created_at=_iso(created),
            ))
            made += 1
        db.commit()

        # ── Call events ──
        for i in range(n_calls):
            created = now - timedelta(days=rnd.randint(0, days - 1), hours=rnd.randint(0, 12), minutes=rnd.randint(0, 59))
            dur = rnd.randint(45, 540)
            ended = created + timedelta(seconds=dur)
            booked = rnd.random() < 0.6
            svc = rnd.choice(service_names)
            sent = rnd.choice(SENTIMENTS)
            tmpl = rnd.choice(SUMMARIES_BOOKED if booked else SUMMARIES_NOBOOK)
            summary = tmpl.format(svc=svc, when=_when_phrase(created + timedelta(days=2)))
            db.add(CallEvent(
                tenant_id=tenant.id,
                call_id=f"call_demo_{i:04d}",
                direction="inbound",
                from_number=f"+9197{rnd.randint(10000000, 99999999)}",
                to_number="+912041234567",
                call_status="analyzed",
                duration_seconds=dur,
                disconnection_reason=rnd.choice(DISCONNECTS),
                user_sentiment=sent,
                call_successful=booked,
                summary=summary,
                transcript=(
                    "Agent: Thanks for calling Glow Salon, this is Bella. How can I help?\n"
                    f"Caller: Hi, I'd like to ask about a {svc.lower()}.\n"
                    "Agent: Of course — I can help with that.\n"
                    + ("Caller: Great, let's book it.\nAgent: Booked! You'll get a text confirmation."
                       if booked else "Caller: Thanks, I'll think about it.\nAgent: No problem, call anytime.")
                ),
                started_at=_iso(created),
                ended_at=_iso(ended),
                created_at=_iso(created),
            ))
        db.commit()

        print(f"Seeded demo tenant '{tenant.slug}': {n_bookings} bookings, {n_calls} calls over {days} days.")
        print(f"View it at:  /portal/{tenant.slug}")
    finally:
        db.close()


def main() -> None:
    p = argparse.ArgumentParser(description="Seed sample calls + bookings for a demo tenant.")
    p.add_argument("--slug", default="demo-glow-salon")
    p.add_argument("--days", type=int, default=30)
    p.add_argument("--calls", type=int, default=55)
    p.add_argument("--bookings", type=int, default=34)
    args = p.parse_args()
    seed(args.slug, args.days, args.calls, args.bookings)


if __name__ == "__main__":
    main()
