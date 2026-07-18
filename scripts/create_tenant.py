"""CLI to build, validate, and provision a tenant's RetellAI agent from a
category template.

Two modes:
  - Existing tenant: pass --slug of a tenant already in the database (e.g.
    one inserted by scripts/seed_dental_tenant.py) to build + provision it.
  - New tenant: pass --slug plus --category/--business-name/... to insert
    the tenant row first, then build + provision.

--dry-run prints the built flow JSON and exits without touching the
database or the Retell API -- always run this first to review the output.

Refuses to re-provision a tenant that already has a retell_agent_id unless
--reprovision is passed explicitly, since Retell's update endpoints haven't
been verified by this codebase -- a --reprovision run creates a NEW,
independent agent/flow rather than mutating the existing live one.

Usage:
    python scripts/create_tenant.py --list-categories
    python scripts/create_tenant.py --slug quensulting-dental --dry-run
    python scripts/create_tenant.py --slug quensulting-dental --reprovision
    python scripts/create_tenant.py --slug glow-salon --category salon_spa \\
        --business-name "Glow Salon & Spa" --address "12 MG Road, Pune" \\
        --service "Haircut" --service "Manicure" --dry-run
"""
from __future__ import annotations

import argparse
import json
import re
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings  # noqa: E402
from app.db import Base, SessionLocal, engine  # noqa: E402
from app.db_models import Service, Tenant  # noqa: E402
from app.flow_builder import build_flow, validate_flow  # noqa: E402
from app.onboarding import TenantValidationError, create_tenant_row, validate_tenant_input  # noqa: E402
from app.provisioning import ProvisioningError, provision_tenant  # noqa: E402
from app.templates.registry import CATEGORY_TEMPLATES, get_template  # noqa: E402

_SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def _parse_weekdays(parser: argparse.ArgumentParser, raw: str) -> list[int]:
    try:
        days = [int(x) for x in raw.split(",") if x.strip() != ""]
    except ValueError:
        parser.error(f"--open-weekdays must be comma-separated integers (Monday=0..Sunday=6), got {raw!r}")
    if not days or any(d < 0 or d > 6 for d in days):
        parser.error(f"--open-weekdays values must be between 0 (Monday) and 6 (Sunday), got {raw!r}")
    return days


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--list-categories", action="store_true",
        help="Print available category keys and display names, then exit",
    )
    parser.add_argument("--slug", help="URL-safe id, e.g. 'glow-salon' (lowercase letters/digits/hyphens)")
    parser.add_argument(
        "--category", default=None, choices=sorted(CATEGORY_TEMPLATES) or None,
        help="Required only when creating a new tenant",
    )
    parser.add_argument("--business-name", default=None)
    parser.add_argument("--timezone", default="Asia/Kolkata")
    parser.add_argument("--open-hour", type=int, default=9)
    parser.add_argument("--close-hour", type=int, default=18)
    parser.add_argument("--open-weekdays", default="0,1,2,3,4,5", help="Comma-separated, Monday=0")
    parser.add_argument("--address", default="")
    parser.add_argument("--transfer-number", default="")
    parser.add_argument("--booking-reference-prefix", default=None)
    parser.add_argument("--notification-email", default="")
    parser.add_argument("--google-sheets-id", default="")
    parser.add_argument(
        "--service", dest="services", action="append", default=[], help="Repeatable: a service name to seed"
    )
    parser.add_argument("--dry-run", action="store_true", help="Build + validate only, no DB write or API call")
    parser.add_argument("--reprovision", action="store_true", help="Allow re-provisioning an already-provisioned tenant")
    args = parser.parse_args()

    if args.list_categories:
        for key in sorted(CATEGORY_TEMPLATES):
            print(f"{key:16s} {CATEGORY_TEMPLATES[key].display_name}")
        return

    if not args.slug:
        parser.error("--slug is required (or pass --list-categories)")
    open_weekdays = _parse_weekdays(parser, args.open_weekdays)

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        tenant = db.query(Tenant).filter_by(slug=args.slug).first()
        if tenant is None:
            if not args.category or not args.business_name:
                parser.error(
                    f"Tenant '{args.slug}' does not exist yet -- --category and "
                    "--business-name are required to create it. Run --list-categories "
                    "to see available categories."
                )
            try:
                if args.dry_run:
                    # Validate only -- build a transient, unpersisted Tenant so
                    # build_flow() below can still read tenant.services, without
                    # ever touching the database.
                    validate_tenant_input(
                        db,
                        slug=args.slug,
                        category=args.category,
                        business_name=args.business_name,
                        open_hour=args.open_hour,
                        close_hour=args.close_hour,
                        open_weekdays=open_weekdays,
                    )
                    tenant = Tenant(
                        slug=args.slug,
                        category=args.category,
                        business_name=args.business_name,
                        timezone=args.timezone,
                        open_hour=args.open_hour,
                        close_hour=args.close_hour,
                        open_weekdays=open_weekdays,
                        address=args.address,
                        transfer_number=args.transfer_number,
                        webhook_secret=secrets.token_urlsafe(24),
                        booking_reference_prefix=(args.booking_reference_prefix or args.slug[:3].upper()),
                        notification_email=args.notification_email,
                        google_sheets_id=args.google_sheets_id,
                    )
                    tenant.services = [
                        Service(name=name, sort_order=i, is_active=True)
                        for i, name in enumerate(args.services)
                    ]
                    print(f"[dry-run] Would create tenant '{tenant.slug}' (category={tenant.category}). Not yet written to the database.")
                else:
                    tenant = create_tenant_row(
                        db,
                        slug=args.slug,
                        category=args.category,
                        business_name=args.business_name,
                        timezone=args.timezone,
                        open_hour=args.open_hour,
                        close_hour=args.close_hour,
                        open_weekdays=open_weekdays,
                        address=args.address,
                        transfer_number=args.transfer_number,
                        booking_reference_prefix=args.booking_reference_prefix,
                        notification_email=args.notification_email,
                        google_sheets_id=args.google_sheets_id,
                        services=args.services,
                    )
                    print(f"Created tenant '{tenant.slug}' (category={tenant.category}).")
            except TenantValidationError as exc:
                parser.error(str(exc))
        else:
            print(f"Using existing tenant '{tenant.slug}' (category={tenant.category}).")

        template = get_template(tenant.category)
        backend_base_url = settings.BACKEND_BASE_URL or "https://YOUR_BACKEND_URL"
        flow = build_flow(tenant, template, backend_base_url)
        validate_flow(flow)

        if args.dry_run:
            print(json.dumps(flow, indent=2))
            print(f"\n[dry-run] Flow built and validated for '{tenant.slug}'. No DB write, no Retell API call.")
            return

        if tenant.retell_agent_id and not args.reprovision:
            parser.error(
                f"Tenant '{tenant.slug}' already has retell_agent_id={tenant.retell_agent_id!r}. "
                "Pass --reprovision to create a new, independent agent/flow anyway."
            )

        if not settings.RETELL_API_KEY:
            parser.error("RETELL_API_KEY is not set -- cannot call the Retell API.")
        if backend_base_url == "https://YOUR_BACKEND_URL":
            parser.error(
                "BACKEND_BASE_URL is not set -- the tool webhook URLs would point at a "
                "placeholder. Set it in .env (or the environment) to your real public host first."
            )

        try:
            result = provision_tenant(
                tenant, template, backend_base_url, settings.RETELL_API_KEY, api_base=settings.RETELL_API_BASE
            )
        except ProvisioningError as exc:
            print(f"Provisioning failed for tenant '{tenant.slug}': {exc}", file=sys.stderr)
            sys.exit(1)
        tenant.retell_voice_id = template.default_voice_id
        tenant.retell_conversation_flow_id = result["conversation_flow_id"]
        tenant.retell_agent_id = result["agent_id"]
        db.commit()
        print(f"Provisioned tenant '{tenant.slug}':")
        print(f"  conversation_flow_id = {result['conversation_flow_id']}")
        print(f"  agent_id             = {result['agent_id']}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
