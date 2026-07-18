"""Home services category template (plumber / electrician / contractor).

default_voice_id verified against a live GET /list-voices call against the
real Retell account this template was provisioned under.
"""
from __future__ import annotations

from .base import CategoryTemplate, ServiceDefault, UrgentBranchCopy

TEMPLATE = CategoryTemplate(
    key="home_services",
    display_name="Home Services (Plumbing / Electrical / Contracting)",
    default_voice_id="11labs-Steve",
    booking_noun="service call",
    agent_persona_name="Jordan",
    role_sentence="the friendly and efficient AI dispatcher taking calls and scheduling service visits",
    customer_noun="customer",
    service_noun="service",
    staff_noun="team",
    scope_disclaimer=(
        "Never give specific technical diagnoses, safety judgments, or "
        "repair cost estimates beyond the general facts above; offer to "
        "have a technician call back or connect the caller to the team for "
        "anything technical."
    ),
    escalation_priority_note=(
        "For active hazards such as gas leaks, electrical sparking, "
        "flooding, or no heat in freezing weather, prioritize connecting "
        "them to the team immediately."
    ),
    urgent_branch=UrgentBranchCopy(
        node_name="Emergency Dispatch",
        instruction_text=(
            "Respond with urgency and calm reassurance. If it is a safety "
            "hazard like a gas leak or electrical fire risk, first advise "
            "them to prioritize their safety (for example, leave the "
            "property, or shut off the main valve or breaker only if it is "
            "safe to do so) before anything else. Explain that "
            "$business_name offers emergency ${booking_noun}s during "
            "working hours ($working_hours_short) and offer to connect "
            "them to the $staff_noun right away to dispatch help as soon "
            "as possible. If it is currently outside working hours, let "
            "them know and offer to take their details for a priority "
            "callback when $business_name opens. Ask whether they would "
            "like you to connect them to the team now."
        ),
        welcome_trigger_prompt=(
            "The caller describes an emergency such as a burst pipe, "
            "flooding, a gas leak, electrical sparking or fire risk, no "
            "heat in freezing weather, or says it is urgent."
        ),
        faq_trigger_prompt=(
            "The caller describes an urgent or emergency home issue such "
            "as flooding, a gas leak, or an electrical hazard."
        ),
        book_instead_prompt=(
            "The caller prefers to book an urgent ${booking_noun} slot and "
            "leave their details instead of being transferred."
        ),
        interruption_sensitivity=1.0,
    ),
    default_services=(
        ServiceDefault(name="General Plumbing Repair"),
        ServiceDefault(name="Drain Cleaning"),
        ServiceDefault(name="Electrical Wiring & Repair"),
        ServiceDefault(name="Water Heater Installation/Repair"),
        ServiceDefault(name="AC/Heating Repair"),
        ServiceDefault(name="General Handyman / Contracting Work"),
    ),
    fact_bullet_labels=(
        ("service_call_fee", "Service call fee"),
        ("emergency_availability", "Emergency availability"),
        ("service_area", "Service area"),
        ("payment_methods", "Payment methods"),
    ),
    extra_slots=(
        {
            "name": "urgency_level",
            "description": (
                "How urgent the issue is, in the caller's own words (e.g. "
                "'routine', 'same day', 'emergency')."
            ),
            "type": "string",
            "required": False,
        },
        {
            "name": "property_type",
            "description": (
                "Whether this is a residential or commercial property, if "
                "mentioned. Empty string if not specified."
            ),
            "type": "string",
            "required": False,
        },
    ),
)
