"""The shape a category template must fill in.

A CategoryTemplate never touches graph structure -- node IDs, edge IDs, and
the overall flow shape live in app/templates/skeleton.py and are identical
across every category. A template only supplies prose and small data lists
that app/flow_builder.py substitutes into that fixed skeleton.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence


@dataclass(frozen=True)
class ServiceDefault:
    """A starter service seeded for a brand-new tenant in this category."""

    name: str
    price_display: str = ""
    duration_minutes: int | None = None


@dataclass(frozen=True)
class UrgentBranchCopy:
    """The one branch that differs most by category -- emergency triage for
    dental, an urgent job request for home services, etc. Node IDs stay
    fixed across every category; only this prose changes.

    instruction_text and book_instead_prompt may reference the same
    $identifiers available to the rest of the skeleton (e.g.
    $working_hours_short, $business_name, $staff_noun, $booking_noun) --
    flow_builder resolves them before the main substitution pass.
    """

    node_name: str
    instruction_text: str
    welcome_trigger_prompt: str
    faq_trigger_prompt: str
    book_instead_prompt: str
    interruption_sensitivity: float = 1.0


@dataclass(frozen=True)
class CategoryTemplate:
    key: str
    display_name: str
    default_voice_id: str

    # Vocabulary substituted throughout the skeleton's prose.
    booking_noun: str  # "appointment" / "reservation" / "booking" / "service call"
    agent_persona_name: str  # "Ava"
    role_sentence: str  # "the friendly and efficient AI front-desk receptionist"
    customer_noun: str  # "patient" / "customer" / "guest"
    service_noun: str  # "dental service" / "service"
    staff_noun: str  # "front desk" / "team" / "office"
    scope_disclaimer: str  # one STYLE-section bullet on what the agent shouldn't advise on
    escalation_priority_note: str  # one ESCALATION-section bullet on what to prioritize

    urgent_branch: UrgentBranchCopy
    default_services: Sequence[ServiceDefault]
    # Ordered (tenant.extra_facts key, spoken label) pairs surfaced as global
    # prompt bullets. A tenant missing a key simply omits that bullet.
    fact_bullet_labels: Sequence[tuple[str, str]]
    # Category-specific extract_dynamic_variables entries appended beyond
    # the 6 fixed ones (patient_name, phone_number, patient_email, service,
    # preferred_datetime, notes). Each dict needs at least "name",
    # "description", "type"; "required" defaults to False. These also get
    # appended to the book_appointment tool's schema so Retell actually
    # captures and sends them -- bookings.py's compute_extra_fields() picks
    # up anything beyond the fixed columns with zero backend code changes.
    extra_slots: Sequence[dict] = field(default_factory=tuple)
