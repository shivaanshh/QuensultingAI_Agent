# Submission — AI Voice Agent Internship (QuensultingAI)

## Deliverables checklist

| # | Required | Status | Where |
|---|----------|--------|-------|
| 1 | Resume (PDF) | ⬜ **You attach this** | — |
| 2 | RetellAI Agent JSON | ✅ | [`retell_conversation_flow.json`](retell_conversation_flow.json) |
| 3 | n8n workflow **or** Python source | ✅ **Both** provided | [`app/`](app/) (primary) + [`n8n_workflow.json`](n8n_workflow.json) (alternative) |
| 4 | Loom walkthrough (3–5 min) | ⬜ **You record this** | script in [`LOOM_SCRIPT.md`](LOOM_SCRIPT.md) |

## Mandatory integrations

| Required | Status | Where |
|----------|--------|-------|
| Save caller info to Google Sheets / Airtable | ✅ Google Sheets | [`app/sheets.py`](app/sheets.py) |
| Confirmation email **or** webhook after booking | ✅ Both (SMTP email + optional outbound webhook) | [`app/notifications.py`](app/notifications.py) |

## Functional requirements → where they're handled

| Requirement | Handled by |
|-------------|-----------|
| Handle inbound calls naturally | `node_welcome` greeting + warm global prompt |
| Book appointments | `collect → extract → check_availability → confirm → book` |
| Answer FAQs | `node_faq` (from clinic facts in the global prompt) |
| Handle interruptions | high `interruption_sensitivity` + global-prompt rules |
| Handle fallback scenarios | `node_booking_failed`, `node_transfer_failed`, `node_suggest_alt` |
| Collect caller details | `node_collect_details` + `node_extract` |
| Escalate / transfer to human | `node_transfer` — a **global node**, reachable from anywhere |

---

## Before you record / submit — the manual steps only you can do

1. **Deploy the backend** to a public URL (see README §"Deploy to the cloud").
2. **Google Sheet**: create it, share (Editor) with the service-account email, put its ID
   in `GOOGLE_SHEETS_ID`, and paste the key into `GOOGLE_CREDENTIALS_JSON`.
3. **Email**: set a Gmail App Password (or any SMTP) in the env vars.
4. **Import** `retell_conversation_flow.json` into Retell → set the two tool URLs to your
   deployed host with `?token=<WEBHOOK_SECRET>` → set a real transfer number → publish.
5. **Test call** from the Retell dashboard; confirm a row lands in the Sheet and an email arrives.
6. **Record the Loom** using `LOOM_SCRIPT.md`; set the link to "anyone with the link can view".

---

## Submission email (copy/paste)

> **To:** hiring@quensultingai.com
> **Subject:** AI Voice Agent Internship Submission – <Your Name>
>
> Hi QuensultingAI team,
>
> Please find my submission for the AI Voice Agent Intern assignment below.
>
> - **RetellAI agent (Conversation Flow):** attached `retell_conversation_flow.json`
> - **Backend source (Python / FastAPI):** <GitHub link — public>
> - **Loom walkthrough (3–5 min):** <Loom link — public>
> - **Resume:** attached PDF
>
> The agent, "Ava", handles inbound calls for QuensultingAI Dental Clinic: it answers
> FAQs, triages emergencies, collects caller details, checks availability against
> working hours, books the appointment (saving to Google Sheets and sending a
> confirmation email), and transfers to a human on request from any point in the call.
> The README covers the architecture and setup, and the backend ships with a passing
> pytest suite.
>
> Happy to walk through any part of the implementation in an interview.
>
> Thank you for the opportunity,
> <Your Name>
> <phone> · <email>
