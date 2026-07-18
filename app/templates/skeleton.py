"""The proven 14-node Retell Conversation Flow graph, parameterized.

This is a transcription of retell_conversation_flow.json (the hand-built,
live-tested dental agent) with prose fields replaced by $identifier
placeholders that app/flow_builder.py resolves per tenant/category.

Node IDs, edge IDs, tool IDs, and the overall graph shape are copied
verbatim and MUST NOT change per category -- that's what lets a rendered
flow be diffed against the original for parity review, and what lets
validate_flow() assert a fixed node-id set regardless of category.

SERVICE_ENUM_SENTINEL marks the three spots (two tool schemas + the
extraction node) where a tenant's live service-name list gets spliced in
structurally after text substitution -- string.Template only substitutes
strings, not lists, so this can't be a $identifier.
"""
from __future__ import annotations

SERVICE_ENUM_SENTINEL = "__SERVICE_ENUM__"

FLOW_SKELETON: dict = {
    "global_prompt": (
        "# ROLE\n"
        "You are $agent_persona_name, $role_sentence for $business_name. You answer "
        "inbound phone calls, answer questions, book ${booking_noun}s, and connect "
        "callers to a human when needed. You sound warm, calm, and natural — like a "
        "helpful person, not a script.\n\n"
        "# BUSINESS FACTS (use ONLY these facts; never invent details)\n"
        "- Business name: $business_name\n"
        "- Working hours: $working_hours_sentence\n"
        "- Location: $location_sentence\n"
        "- Services: $services_sentence.\n"
        "$facts_bullets\n\n"
        "# STYLE\n"
        "- Keep replies short and conversational — usually one or two sentences. "
        "This is a phone call, not an essay.\n"
        "- Ask only ONE question at a time.\n"
        "- When you take a name, confirm the spelling if it sounds unusual. When you "
        "take a phone number, read it back to confirm.\n"
        "- $scope_disclaimer\n"
        "- If you are unsure or the caller asks something you cannot handle, offer "
        "to connect them to the $staff_noun instead of guessing.\n"
        "- Only offer ${booking_noun} times within working hours ($working_hours_short).\n\n"
        "# INTERRUPTIONS & CORRECTIONS\n"
        "- If the caller interrupts you, stop talking immediately and listen.\n"
        "- If the caller corrects a detail (name, number, time, service), accept the "
        "correction gracefully and confirm the new value.\n\n"
        "# ESCALATION\n"
        "- At ANY point, if the caller asks for a human, a real person, staff, or "
        "the $staff_noun, connect them.\n"
        "- $escalation_priority_note"
    ),
    "model_choice": {"type": "cascading", "model": "gpt-4.1"},
    "model_temperature": 0.3,
    "start_speaker": "agent",
    "start_node_id": "node_welcome",
    "begin_tag_display_position": {"x": -240, "y": 40},
    "default_dynamic_variables": {
        # Overwritten by flow_builder with the real tenant values -- kept
        # here only so the skeleton is a structurally complete flow on its own.
        "business_name": "$business_name",
        "human_agent_number": "",
    },
    "tools": [
        {
            "tool_id": "tool_check_availability",
            "type": "custom",
            "name": "check_availability",
            "description": (
                "Checks whether a requested $booking_noun date/time falls within "
                "$business_name's working hours and is available. Call this AFTER "
                "the caller's name, phone, service, and preferred time have been "
                "collected, and BEFORE confirming the booking."
            ),
            "url": "$check_availability_url",
            "method": "POST",
            "speak_during_execution": True,
            "execution_message_type": "static_text",
            "execution_message_description": "Let me check our availability for that time.",
            "speak_after_execution": False,
            "timeout_ms": 15000,
            "parameters": {
                "type": "object",
                "properties": {
                    "preferred_datetime": {
                        "type": "string",
                        "description": (
                            "The caller's preferred $booking_noun date and time, in "
                            "natural language (e.g. 'next Monday at 3pm')."
                        ),
                    },
                    "service": {
                        "type": "string",
                        "description": f"The $service_noun requested.",
                        "enum": SERVICE_ENUM_SENTINEL,
                    },
                },
                "required": ["preferred_datetime", "service"],
            },
            "response_variables": {
                "slot_available": "available",
                "availability_reason": "reason",
                "suggested_slots": "suggested_slots",
            },
        },
        {
            "tool_id": "tool_book_appointment",
            "type": "custom",
            "name": "book_appointment",
            "description": (
                "Books a $booking_noun by sending the caller's details to the "
                "$business_name backend, which saves the record and sends a "
                "confirmation. Call this ONLY after the caller has verbally "
                "confirmed all details are correct."
            ),
            "url": "$book_appointment_url",
            "method": "POST",
            "speak_during_execution": True,
            "execution_message_type": "static_text",
            "execution_message_description": "Perfect, I'm booking that for you now — one moment.",
            "speak_after_execution": False,
            "timeout_ms": 20000,
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_name": {
                        "type": "string",
                        "description": "Full name of the $customer_noun.",
                    },
                    "phone_number": {
                        "type": "string",
                        "description": "Caller's callback phone number.",
                    },
                    "patient_email": {
                        "type": "string",
                        "description": (
                            "Caller's email for the confirmation email. Empty "
                            "string if they declined."
                        ),
                    },
                    "service": {
                        "type": "string",
                        "description": "The $service_noun requested.",
                        "enum": SERVICE_ENUM_SENTINEL,
                    },
                    "preferred_datetime": {
                        "type": "string",
                        "description": "Confirmed $booking_noun date and time in natural language.",
                    },
                    "notes": {
                        "type": "string",
                        "description": "Any extra notes from the caller. Empty string if none.",
                    },
                },
                "required": ["patient_name", "phone_number", "service", "preferred_datetime"],
            },
            "response_variables": {
                "booking_status": "status",
                "booking_reference": "booking_reference",
                "confirmed_datetime": "confirmed_datetime",
            },
        },
    ],
    "nodes": [
        {
            "id": "node_welcome",
            "type": "conversation",
            "name": "Welcome & Intent",
            "display_position": {"x": 0, "y": 0},
            "instruction": {
                "type": "prompt",
                "text": (
                    "Warmly greet the caller: 'Thank you for calling $business_name, "
                    "this is $agent_persona_name. How can I help you today?' Then "
                    "listen and identify what they need. If their intent is unclear, "
                    "ask a brief clarifying question. Do not answer detailed "
                    "questions here — just identify the intent."
                ),
            },
            "interruption_sensitivity": 0.9,
            "edges": [
                {
                    "id": "edge_welcome_book",
                    "transition_condition": {
                        "type": "prompt",
                        "prompt": "The caller wants to book, schedule, reschedule, or change a ${booking_noun}.",
                    },
                    "destination_node_id": "node_collect_details",
                },
                {
                    "id": "edge_welcome_faq",
                    "transition_condition": {
                        "type": "prompt",
                        "prompt": (
                            "The caller asks a general question about the business "
                            "such as timings, location, fees, services, payment "
                            "methods, or policies."
                        ),
                    },
                    "destination_node_id": "node_faq",
                },
                {
                    "id": "edge_welcome_emergency",
                    "transition_condition": {"type": "prompt", "prompt": "$urgent_welcome_trigger"},
                    "destination_node_id": "node_emergency",
                },
            ],
        },
        {
            "id": "node_faq",
            "type": "conversation",
            "name": "Answer FAQs",
            "display_position": {"x": 380, "y": -220},
            "instruction": {
                "type": "prompt",
                "text": (
                    "Answer the caller's question using ONLY the facts in the "
                    "global prompt above (hours, location, services, and other "
                    "policies). Be concise and friendly. Answer any follow-up "
                    "questions the same way. When the caller seems satisfied, ask: "
                    "'Would you like to book a $booking_noun, or is there anything "
                    "else I can help with?'"
                ),
            },
            "interruption_sensitivity": 0.9,
            "edges": [
                {
                    "id": "edge_faq_book",
                    "transition_condition": {
                        "type": "prompt",
                        "prompt": "The caller wants to book or schedule a ${booking_noun}.",
                    },
                    "destination_node_id": "node_collect_details",
                },
                {
                    "id": "edge_faq_emergency",
                    "transition_condition": {"type": "prompt", "prompt": "$urgent_faq_trigger"},
                    "destination_node_id": "node_emergency",
                },
                {
                    "id": "edge_faq_done",
                    "transition_condition": {
                        "type": "prompt",
                        "prompt": "The caller has no further questions and does not want to book anything.",
                    },
                    "destination_node_id": "node_goodbye",
                },
            ],
        },
        {
            "id": "node_emergency",
            "type": "conversation",
            "name": "$urgent_node_name",
            "display_position": {"x": 380, "y": 200},
            "instruction": {"type": "prompt", "text": "$urgent_instruction_text"},
            "interruption_sensitivity": 1.0,
            "edges": [
                {
                    "id": "edge_emergency_transfer",
                    "transition_condition": {
                        "type": "prompt",
                        "prompt": "The caller wants to be connected to staff or the $staff_noun now.",
                    },
                    "destination_node_id": "node_transfer",
                },
                {
                    "id": "edge_emergency_book",
                    "transition_condition": {"type": "prompt", "prompt": "$urgent_book_instead_prompt"},
                    "destination_node_id": "node_collect_details",
                },
            ],
        },
        {
            "id": "node_collect_details",
            "type": "conversation",
            "name": "Collect Caller Details",
            "display_position": {"x": 760, "y": 0},
            "instruction": {
                "type": "prompt",
                "text": (
                    "Collect the following one at a time, in a natural "
                    "conversational way. Do NOT ask for more than one thing per "
                    "turn.\n"
                    "1. The $customer_noun's full name. Confirm the spelling if it "
                    "sounds unusual.\n"
                    "2. The best callback phone number. Read it back to confirm it "
                    "is correct.\n"
                    "3. Their email address for the confirmation email. This is "
                    "optional — if they decline, that is fine, move on.\n"
                    "4. Which service they need. If they are unsure, briefly list "
                    "the services offered.\n"
                    "5. Their preferred day and time for the $booking_noun. Remind "
                    "them $business_name is open $working_hours_short.\n"
                    "Handle interruptions and corrections gracefully. Do not "
                    "proceed until you have at least the name, phone number, "
                    "service, and preferred day/time."
                ),
            },
            "interruption_sensitivity": 0.8,
            "edges": [
                {
                    "id": "edge_collect_extract",
                    "transition_condition": {
                        "type": "prompt",
                        "prompt": (
                            "The caller's name, phone number, service, and "
                            "preferred day/time have all been collected."
                        ),
                    },
                    "destination_node_id": "node_extract",
                }
            ],
        },
        {
            "id": "node_extract",
            "type": "extract_dynamic_variables",
            "name": "Extract Booking Details",
            "display_position": {"x": 1140, "y": 0},
            "variables": [
                {
                    "type": "string",
                    "name": "patient_name",
                    "description": "The $customer_noun's full name.",
                    "examples": ["Priya Sharma", "Rahul Verma"],
                    "required": True,
                },
                {
                    "type": "string",
                    "name": "phone_number",
                    "description": "The caller's callback phone number, digits only where possible.",
                    "examples": ["+919812345678", "9812345678"],
                    "required": True,
                },
                {
                    "type": "string",
                    "name": "patient_email",
                    "description": "The caller's email address for confirmation. Empty if they declined.",
                    "examples": ["priya@example.com"],
                    "required": False,
                },
                {
                    "type": "enum",
                    "name": "service",
                    "description": "The $service_noun requested.",
                    "choices": SERVICE_ENUM_SENTINEL,
                    "required": True,
                },
                {
                    "type": "string",
                    "name": "preferred_datetime",
                    "description": "The caller's preferred $booking_noun date and time, in natural language.",
                    "examples": ["Monday at 3 pm", "tomorrow morning around 10"],
                    "required": True,
                },
                {
                    "type": "string",
                    "name": "notes",
                    "description": "Any extra notes or requests from the caller. Empty if none.",
                    "required": False,
                },
            ],
            "edges": [
                {
                    "id": "edge_extract_availability",
                    "transition_condition": {"type": "prompt", "prompt": "Booking details have been extracted."},
                    "destination_node_id": "node_check_availability",
                }
            ],
            "else_edge": {
                "id": "edge_extract_else",
                "transition_condition": {"type": "prompt", "prompt": "Else"},
                "destination_node_id": "node_check_availability",
            },
        },
        {
            "id": "node_check_availability",
            "type": "function",
            "name": "Check Availability",
            "display_position": {"x": 1520, "y": 0},
            "tool_id": "tool_check_availability",
            "tool_type": "local",
            "wait_for_result": True,
            "speak_during_execution": True,
            "instruction": {"type": "static_text", "text": "Let me check our availability for that time."},
            "edges": [
                {
                    "id": "edge_avail_yes",
                    "transition_condition": {
                        "type": "equation",
                        "equations": [{"left": "{{slot_available}}", "operator": "==", "right": "true"}],
                        "operator": "&&",
                    },
                    "destination_node_id": "node_confirm",
                }
            ],
            "else_edge": {
                "id": "edge_avail_no",
                "transition_condition": {"type": "prompt", "prompt": "Else"},
                "destination_node_id": "node_suggest_alt",
            },
        },
        {
            "id": "node_suggest_alt",
            "type": "conversation",
            "name": "Suggest Alternative Time",
            "display_position": {"x": 1520, "y": 300},
            "instruction": {
                "type": "prompt",
                "text": (
                    "The requested $booking_noun time is not available or falls "
                    "outside working hours. Politely explain this. If suggested "
                    "alternative slots are available in {{suggested_slots}}, offer "
                    "them. Otherwise remind the caller $business_name is open "
                    "$working_hours_short, and ask them to pick a different day "
                    "and time."
                ),
            },
            "interruption_sensitivity": 0.8,
            "edges": [
                {
                    "id": "edge_alt_retry",
                    "transition_condition": {
                        "type": "prompt",
                        "prompt": "The caller provides a new preferred day and time.",
                    },
                    "destination_node_id": "node_extract",
                },
                {
                    "id": "edge_alt_giveup",
                    "transition_condition": {
                        "type": "prompt",
                        "prompt": (
                            "The caller does not want to pick another time and "
                            "would like to end or call back later."
                        ),
                    },
                    "destination_node_id": "node_goodbye",
                },
            ],
        },
        {
            "id": "node_confirm",
            "type": "conversation",
            "name": "Confirm Details",
            "display_position": {"x": 1900, "y": 0},
            "instruction": {
                "type": "prompt",
                "text": (
                    "Read back the $booking_noun details for confirmation, warmly "
                    "and clearly: name {{patient_name}}, phone number "
                    "{{phone_number}}, service {{service}}, and preferred time "
                    "{{preferred_datetime}}. Then ask: 'Does that all look "
                    "correct?' Wait for the caller to confirm before proceeding."
                ),
            },
            "interruption_sensitivity": 0.8,
            "edges": [
                {
                    "id": "edge_confirm_book",
                    "transition_condition": {
                        "type": "prompt",
                        "prompt": "The caller confirms all the details are correct.",
                    },
                    "destination_node_id": "node_book",
                },
                {
                    "id": "edge_confirm_edit",
                    "transition_condition": {
                        "type": "prompt",
                        "prompt": "The caller wants to change or correct one or more details.",
                    },
                    "destination_node_id": "node_collect_details",
                },
            ],
        },
        {
            "id": "node_book",
            "type": "function",
            "name": "Book Appointment",
            "display_position": {"x": 2280, "y": 0},
            "tool_id": "tool_book_appointment",
            "tool_type": "local",
            "wait_for_result": True,
            "speak_during_execution": True,
            "instruction": {"type": "static_text", "text": "Perfect, I'm booking that for you now — one moment."},
            "edges": [
                {
                    "id": "edge_book_success",
                    "transition_condition": {
                        "type": "equation",
                        "equations": [{"left": "{{booking_status}}", "operator": "==", "right": "success"}],
                        "operator": "&&",
                    },
                    "destination_node_id": "node_booking_success",
                }
            ],
            "else_edge": {
                "id": "edge_book_failed",
                "transition_condition": {"type": "prompt", "prompt": "Else"},
                "destination_node_id": "node_booking_failed",
            },
        },
        {
            "id": "node_booking_success",
            "type": "conversation",
            "name": "Booking Confirmed",
            "display_position": {"x": 2660, "y": -200},
            "instruction": {
                "type": "prompt",
                "text": (
                    "Cheerfully confirm the $booking_noun is booked. Give the "
                    "booking reference {{booking_reference}} and the confirmed "
                    "time {{confirmed_datetime}}. If the caller gave an email, "
                    "mention a confirmation email is on its way. Then ask: 'Is "
                    "there anything else I can help you with?'"
                ),
            },
            "interruption_sensitivity": 0.9,
            "edges": [
                {
                    "id": "edge_success_another",
                    "transition_condition": {
                        "type": "prompt",
                        "prompt": "The caller wants to book another $booking_noun or asks another question.",
                    },
                    "destination_node_id": "node_welcome",
                },
                {
                    "id": "edge_success_done",
                    "transition_condition": {
                        "type": "prompt",
                        "prompt": "The caller has nothing else and is ready to end the call.",
                    },
                    "destination_node_id": "node_goodbye",
                },
            ],
        },
        {
            "id": "node_booking_failed",
            "type": "conversation",
            "name": "Booking Failed Fallback",
            "display_position": {"x": 2660, "y": 220},
            "instruction": {
                "type": "prompt",
                "text": (
                    "Apologize sincerely that the $booking_noun could not be "
                    "completed right now due to a system issue. Reassure the "
                    "caller that their details have been noted. Offer to connect "
                    "them to the $staff_noun to finish the booking, or to have "
                    "someone call them back. Do not promise the $booking_noun is "
                    "confirmed."
                ),
            },
            "interruption_sensitivity": 0.9,
            "edges": [
                {
                    "id": "edge_failed_transfer",
                    "transition_condition": {
                        "type": "prompt",
                        "prompt": "The caller wants to be connected to the $staff_noun to complete the booking.",
                    },
                    "destination_node_id": "node_transfer",
                },
                {
                    "id": "edge_failed_callback",
                    "transition_condition": {
                        "type": "prompt",
                        "prompt": "The caller would rather call back later or is fine ending the call.",
                    },
                    "destination_node_id": "node_goodbye",
                },
            ],
        },
        {
            "id": "node_transfer",
            "type": "transfer_call",
            "name": "Transfer to Human",
            "display_position": {"x": 2280, "y": 460},
            "global_node_setting": {
                "condition": (
                    "The caller asks to speak to a human, a real person, a staff "
                    "member, the receptionist, or the $staff_noun at any point in "
                    "the conversation."
                ),
                "cool_down": 2,
            },
            "transfer_destination": {"type": "predefined", "number": "{{human_agent_number}}"},
            "transfer_option": {"type": "cold_transfer", "cold_transfer_mode": "sip_refer"},
            "speak_during_execution": True,
            "instruction": {
                "type": "static_text",
                "text": "Sure, let me connect you to our $staff_noun now. Please stay on the line — one moment.",
            },
            "edge": {
                "id": "edge_transfer_failed",
                "transition_condition": {"type": "prompt", "prompt": "Transfer failed"},
                "destination_node_id": "node_transfer_failed",
            },
        },
        {
            "id": "node_transfer_failed",
            "type": "conversation",
            "name": "Transfer Failed Fallback",
            "display_position": {"x": 2660, "y": 620},
            "instruction": {
                "type": "prompt",
                "text": (
                    "The transfer did not go through. Apologize, and let the "
                    "caller know the $staff_noun can be reached during working "
                    "hours ($working_hours_short). Offer to note down a callback "
                    "number and a short message for the team, or suggest they "
                    "call back shortly. Keep it brief and reassuring."
                ),
            },
            "interruption_sensitivity": 0.9,
            "edges": [
                {
                    "id": "edge_transferfail_done",
                    "transition_condition": {"type": "prompt", "prompt": "The caller is ready to end the call."},
                    "destination_node_id": "node_goodbye",
                }
            ],
        },
        {
            "id": "node_goodbye",
            "type": "conversation",
            "name": "Goodbye",
            "display_position": {"x": 3040, "y": 0},
            "instruction": {
                "type": "prompt",
                "text": (
                    "Warmly wrap up the call. If a $booking_noun was made, "
                    "briefly remind them of the day and time. Thank them for "
                    "calling $business_name and wish them a great day."
                ),
            },
            "interruption_sensitivity": 0.9,
            "edges": [
                {
                    "id": "edge_goodbye_more",
                    "transition_condition": {
                        "type": "prompt",
                        "prompt": "The caller brings up something new or asks another question.",
                    },
                    "destination_node_id": "node_welcome",
                }
            ],
            "else_edge": {
                "id": "edge_goodbye_end",
                "transition_condition": {"type": "prompt", "prompt": "Else"},
                "destination_node_id": "node_end",
            },
        },
        {
            "id": "node_end",
            "type": "end",
            "name": "End Call",
            "display_position": {"x": 3420, "y": 0},
            "speak_during_execution": False,
        },
    ],
}
