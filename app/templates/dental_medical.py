"""Dental / medical clinic category template.

Transcribed from the original hand-built, live-tested
retell_conversation_flow.json (see repo root) -- this is the reference
template the other three verticals are checked against for shape parity.
Rendering this template for the "quensulting-dental" tenant should produce
a flow that reads, structurally and semantically, the same as that
original file (see the parity-check step in the implementation plan).
"""
from __future__ import annotations

from .base import CategoryTemplate, ServiceDefault, UrgentBranchCopy

TEMPLATE = CategoryTemplate(
    key="dental_medical",
    display_name="Dental / Medical Clinic",
    # Verified real via a live GET /list-voices call and a successful
    # create-agent call for the quensulting-dental tenant.
    default_voice_id="11labs-Adrian",
    booking_noun="appointment",
    agent_persona_name="Ava",
    role_sentence="the friendly and efficient AI front-desk receptionist",
    customer_noun="patient",
    service_noun="dental service",
    staff_noun="front desk",
    scope_disclaimer=(
        "Never give clinical or medical advice beyond the general facts "
        "above. For clinical questions, offer to have a dentist call back "
        "or connect the caller to staff."
    ),
    escalation_priority_note=(
        "For emergencies with severe pain, bleeding, swelling, or trauma, "
        "prioritize connecting them to staff quickly."
    ),
    urgent_branch=UrgentBranchCopy(
        node_name="Emergency Triage",
        instruction_text=(
            "Respond with empathy. Explain that $business_name keeps "
            "same-day emergency slots during working hours "
            "($working_hours_short) and that you can connect them to the "
            "$staff_noun right away to be seen as soon as possible. If it "
            "is currently outside working hours, gently advise them to "
            "seek the nearest emergency dental or medical care, and offer "
            "to take their details for an urgent callback when "
            "$business_name opens. Ask whether they would like you to "
            "connect them to staff now."
        ),
        welcome_trigger_prompt=(
            "The caller describes a dental emergency, severe pain, "
            "bleeding, swelling, a knocked-out or broken tooth, or says it "
            "is urgent."
        ),
        faq_trigger_prompt="The caller describes a dental emergency or urgent pain.",
        book_instead_prompt=(
            "The caller prefers to book an urgent ${booking_noun} slot and "
            "leave their details instead of being transferred."
        ),
        interruption_sensitivity=1.0,
    ),
    default_services=(
        ServiceDefault(name="Dental Cleaning"),
        ServiceDefault(name="Root Canal Treatment"),
        ServiceDefault(name="Teeth Whitening"),
        ServiceDefault(name="Braces Consultation"),
        ServiceDefault(name="Tooth Extraction"),
        ServiceDefault(name="General Dental Consultation", price_display="₹500"),
    ),
    fact_bullet_labels=(
        ("consultation_fee", "General consultation fee"),
        ("walk_ins", "Walk-ins"),
        ("emergency_slots", "Emergency appointments"),
        ("payment_methods", "Payment methods"),
    ),
)
