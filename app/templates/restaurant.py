"""Restaurant category template.

"Services" in the shared skeleton map to bookable dining options here
(table for dinner, private dining, takeaway, ...) rather than literal
services -- this reuses the same enum/extraction mechanism without any
skeleton changes. party_size is the canonical extra_slots example from the
original plan: it lands in Booking.extra_fields automatically via
app/bookings.py's compute_extra_fields(), no backend change needed.

default_voice_id verified against a live GET /list-voices call against the
real Retell account this template was provisioned under.
"""
from __future__ import annotations

from .base import CategoryTemplate, ServiceDefault, UrgentBranchCopy

TEMPLATE = CategoryTemplate(
    key="restaurant",
    display_name="Restaurant",
    default_voice_id="11labs-Ethan",
    booking_noun="reservation",
    agent_persona_name="Leo",
    role_sentence="the friendly and efficient AI host taking reservations and calls",
    customer_noun="guest",
    service_noun="reservation type",
    staff_noun="host stand",
    scope_disclaimer=(
        "Never make promises about specific menu availability, ingredient "
        "substitutions, or allergen safety beyond the general facts above; "
        "offer to have the manager or chef call back for detailed dietary "
        "questions."
    ),
    escalation_priority_note=(
        "For large party requests (8 or more guests), private events, or "
        "any food-safety or allergy concern, prioritize connecting them to "
        "staff quickly."
    ),
    urgent_branch=UrgentBranchCopy(
        node_name="Large Party / Urgent Request",
        instruction_text=(
            "Acknowledge the request warmly. Explain that for parties of 8 "
            "or more, private events, or urgent food-safety or allergy "
            "concerns, it's best for the $staff_noun to confirm the "
            "details directly. Offer to connect them to the $staff_noun "
            "now, during working hours ($working_hours_short). Ask whether "
            "they would like you to connect them to staff now."
        ),
        welcome_trigger_prompt=(
            "The caller requests a large party of 8 or more guests, a "
            "private event booking, or describes an urgent food-safety or "
            "allergy concern that needs immediate staff attention."
        ),
        faq_trigger_prompt=(
            "The caller describes a large party of 8 or more guests, a "
            "private event request, or an urgent food-safety or allergy "
            "concern."
        ),
        book_instead_prompt=(
            "The caller prefers to leave their details for a large party "
            "or event ${booking_noun} instead of being transferred right now."
        ),
        interruption_sensitivity=1.0,
    ),
    default_services=(
        ServiceDefault(name="Table for Dinner"),
        ServiceDefault(name="Table for Lunch"),
        ServiceDefault(name="Private Dining / Event Booking"),
        ServiceDefault(name="Outdoor Seating"),
        ServiceDefault(name="Weekend Brunch"),
        ServiceDefault(name="Takeaway / Pickup Order"),
    ),
    fact_bullet_labels=(
        ("cuisine_highlights", "Cuisine & specialties"),
        ("dietary_options", "Dietary options"),
        ("dress_code", "Dress code"),
        ("payment_methods", "Payment methods"),
    ),
    extra_slots=(
        {
            "name": "party_size",
            "description": "Number of guests in the party, as a number.",
            "type": "string",
            "required": True,
        },
        {
            "name": "occasion",
            "description": (
                "Special occasion being celebrated, if mentioned (e.g. "
                "birthday, anniversary). Empty string if none."
            ),
            "type": "string",
            "required": False,
        },
    ),
)
