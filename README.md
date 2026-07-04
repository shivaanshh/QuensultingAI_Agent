# QuensultingAI Dental Clinic — AI Receptionist Voice Agent

An inbound voice agent for a dental clinic, built on **RetellAI Conversational Flow**
with a **FastAPI** automation backend that saves every booking to **Google Sheets**
and sends a **confirmation email** (plus an optional outbound webhook).

The agent — "Ava" — answers calls, handles FAQs, triages emergencies, collects
caller details, checks availability against working hours, books the appointment,
and transfers to a human whenever asked.

---

## 1. Architecture

```
   ┌──────────────┐     voice      ┌─────────────────────────┐
   │   Caller     │ ─────────────▶ │      RetellAI            │
   │  (phone)     │ ◀───────────── │  Conversation Flow       │
   └──────────────┘                │  (retell_conversation_   │
                                   │        flow.json)        │
                                   └───────────┬─────────────┘
                                               │ HTTPS (custom tools)
                          check-availability   │   book-appointment
                                               ▼
                                   ┌─────────────────────────┐
                                   │     FastAPI backend      │
                                   │        (app/)            │
                                   └───┬─────────┬─────────┬──┘
                                       │         │         │
                             ┌─────────▼──┐  ┌───▼────┐  ┌─▼──────────────┐
                             │  Google    │  │  SMTP  │  │ Optional        │
                             │  Sheets    │  │  email │  │ outbound webhook│
                             │ (bookings) │  │        │  │ (n8n/Zapier/CRM)│
                             └────────────┘  └────────┘  └────────────────┘
```

**Why this shape.** The conversation logic lives entirely in the RetellAI graph
(nodes + edges), so it's inspectable and versioned in the dashboard. The backend
is a thin, stateless set of webhooks — it validates input, enforces business rules
(working hours), persists the record, and notifies. Google Sheets is the single
source of truth; email and the outbound webhook are best-effort and never block a
booking.

---

## 2. Conversation flow

Start speaker is the **agent** (it greets on pickup). Fifteen nodes:

```
                              ┌──────────────┐
                              │ node_welcome │  greet + detect intent
                              └──┬───┬────┬──┘
              books ────────────┘   │    └──────────── emergency
                                    │ FAQ
        ┌───────────────┐    ┌──────▼─────┐    ┌────────────────┐
        │ node_collect_ │◀───│  node_faq  │    │ node_emergency │
        │   details     │    └──────┬─────┘    └───┬────────┬───┘
        └──────┬────────┘           │ done         │ book   │ transfer
               │                    ▼              │        │
        ┌──────▼────────┐    ┌────────────┐        │        │
        │ node_extract  │    │node_goodbye│◀───────┘        │
        │ (dyn. vars)   │    └──────┬─────┘                 │
        └──────┬────────┘           ▼                       │
               ▼               ┌─────────┐                  │
      ┌────────────────────┐   │node_end │                  │
      │node_check_availab. │   └─────────┘                  │
      │  (function tool)   │                                │
      └───┬────────────┬───┘                                │
   avail  │            │ not available                      │
          ▼            ▼                                     │
   ┌────────────┐  ┌──────────────────┐                     │
   │node_confirm│  │ node_suggest_alt │──▶ back to extract  │
   └─────┬──────┘  └──────────────────┘                     │
    yes  │  edit ──▶ back to collect                         │
         ▼                                                   │
   ┌────────────┐  success  ┌────────────────────┐          │
   │  node_book │──────────▶│node_booking_success│          │
   │ (function) │           └────────────────────┘          │
   └─────┬──────┘                                            │
    fail │                                                   │
         ▼                                                   ▼
   ┌────────────────────┐   transfer   ┌────────────────────────┐
   │node_booking_failed │─────────────▶│     node_transfer      │◀── GLOBAL:
   └────────────────────┘              │ (transfer_call → human)│    "I want a
                                       └───────────┬────────────┘    human" from
                                          transfer │ failed           anywhere
                                                    ▼
                                       ┌────────────────────────┐
                                       │  node_transfer_failed  │
                                       └────────────────────────┘
```

Design choices worth calling out:

- **Intent routing at the top.** `node_welcome` only classifies intent and branches;
  it never answers questions itself. This keeps each node focused and easy to tune.
- **Deterministic gates via equation edges.** Availability and booking outcomes use
  `equation` transition conditions (`{{slot_available}} == "true"`,
  `{{booking_status}} == "success"`) instead of prompt-based guesses, so the branch
  is driven by real backend data, not the model's interpretation.
- **`extract_dynamic_variables` before booking.** Collected details are pinned to
  dynamic variables (`{{patient_name}}`, etc.) so the confirmation node can read them
  back verbatim, and corrections loop cleanly back to collection.
- **Availability check before confirmation.** The agent never confirms a slot that's
  outside Mon–Sat 9–6; out-of-hours requests route to `node_suggest_alt` with
  concrete alternatives from the backend.
- **A global transfer node.** `node_transfer` has a `global_node_setting`, so "let me
  talk to a person" works from *any* node — the core escalation requirement.
- **Explicit fallbacks.** Booking failure (`node_booking_failed`) and transfer failure
  (`node_transfer_failed`) are real nodes, not dead ends. Conversation nodes omit an
  `else_edge` on purpose so they self-handle ambiguity by re-asking within the node.
- **Interruption handling.** `interruption_sensitivity` is raised on the talk-heavy
  nodes (0.9–1.0) so the agent yields the moment the caller speaks; the global prompt
  reinforces stopping and accepting corrections.

---

## 3. Repository layout

```
quensulting-dental-voice-agent/
├── retell_conversation_flow.json   # THE Retell agent (import this)
├── app/
│   ├── main.py            # FastAPI app + webhook routes
│   ├── config.py          # env-driven settings
│   ├── models.py          # pydantic request/response schemas
│   ├── utils.py           # booking refs + working-hours logic
│   ├── sheets.py          # Google Sheets persistence
│   └── notifications.py   # SMTP email + optional webhook
├── tests/                 # pytest suite (23 tests, no external services)
│   ├── test_utils.py
│   └── test_api.py
├── n8n_workflow.json      # alternative booking automation (importable n8n)
├── Dockerfile             # container image
├── render.yaml            # one-click Render.com Blueprint deploy
├── Procfile               # Railway / Heroku-style deploy
├── requirements.txt
├── requirements-dev.txt   # requirements + pytest
├── .env.example
├── SUBMISSION.md          # deliverables checklist + submission email
├── RUN_LOCAL.md           # local + ngrok quick-demo walkthrough
├── N8N_SETUP.md           # how to import/configure the n8n workflow
├── LOOM_SCRIPT.md         # walkthrough script for the recording
└── README.md
```

> **Automation: two options.** The primary automation is the Python/FastAPI backend in
> `app/` (it also does the availability logic and has tests). `n8n_workflow.json` is an
> alternative implementation of the booking step (webhook → Google Sheets → email) —
> see `N8N_SETUP.md`. Use one or the other for the `book_appointment` tool URL.

### Run the tests

```bash
pip install -r requirements-dev.txt
pytest -q          # 23 passing; stubs Sheets/email, needs no credentials
```

### Deploy to the cloud (so Retell can reach it)

The backend needs a public HTTPS URL. Three options:

- **Render** — push this repo, create a *Blueprint* from `render.yaml`, and fill in the
  secret env vars. Paste your whole service-account key into `GOOGLE_CREDENTIALS_JSON`.
- **Railway / Fly / Heroku** — the `Procfile` works as-is; set the same env vars.
- **Docker** — `docker build -t dental . && docker run -p 8000:8000 --env-file .env dental`.
- **Local + ngrok** — for a quick demo: `uvicorn app.main:app` then `ngrok http 8000`.

> On cloud hosts you usually can't upload the `google-credentials.json` file. Use
> `GOOGLE_CREDENTIALS_JSON` instead — paste the entire key JSON into that one env var.

---

## 4. Setup

### 4.1 Backend

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then fill in the values (see below)
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Expose it publicly so Retell can reach it. During development:

```bash
ngrok http 8000               # gives you https://<subdomain>.ngrok-free.app
```

Health check: `GET https://<your-host>/health`.

### 4.2 Google Sheets

1. In Google Cloud, create a **service account** and download its JSON key as
   `google-credentials.json` (place it in the project root).
2. Enable the **Google Sheets API** for that project.
3. Create a Google Sheet and **share it (Editor)** with the service account email
   (`...@....iam.gserviceaccount.com`).
4. Put the sheet ID (from its URL) in `.env` as `GOOGLE_SHEETS_ID`.

The `Bookings` worksheet and header row are created automatically on first write.

### 4.3 Email (SMTP)

For Gmail: turn on 2-factor auth, create an **App Password**, and use it as
`SMTP_PASSWORD`. Any SMTP provider (SendGrid, SES, Mailgun) works by changing
`SMTP_HOST`/`SMTP_PORT`/credentials. Leave these blank and email is simply skipped.

### 4.4 Import the RetellAI agent

1. In the Retell dashboard: **Create Agent → Conversation Flow → Import**, and upload
   `retell_conversation_flow.json`.
2. Open the two custom tools (`check_availability`, `book_appointment`) and replace
   `https://YOUR_BACKEND_URL` with your real host, appending the secret token, e.g.
   `https://<your-host>/webhook/book-appointment?token=<WEBHOOK_SECRET>`.
3. Set `node_transfer`'s number (the `{{human_agent_number}}` default) to a real
   front-desk number, pick a voice, attach a phone number, and publish.
4. (Optional) Set the agent-level **Webhook URL** to
   `https://<your-host>/webhook/retell-events` to log call lifecycle events.

> **Note on `tool_type`.** The two function nodes reference flow-level tools with
> `"tool_type": "local"`. If the import ever complains that a function node isn't
> linked, just re-select the tool in that node's dropdown in the UI — the tool
> definition itself is already in the file.

---

## 5. API reference

| Method | Path | Purpose |
|---|---|---|
| GET  | `/health` | Liveness check |
| POST | `/webhook/check-availability` | Custom tool — returns `{available, reason, suggested_slots}` |
| POST | `/webhook/book-appointment` | Custom tool — persists + notifies, returns `{status, booking_reference, confirmed_datetime}` |
| POST | `/webhook/retell-events` | Optional agent webhook — logs `call_started/ended/analyzed` |

Both tool endpoints accept Retell's `{ "call": {...}, "args": {...} }` envelope and
also a flat body (`args_at_root=true`). They're protected by a shared `?token=` secret.

### Example (what Retell sends → what it gets back)

```jsonc
// POST /webhook/book-appointment?token=...
{ "call": { "call_id": "abc" },
  "name": "book_appointment",
  "args": { "patient_name": "Priya Sharma", "phone_number": "9812345678",
            "patient_email": "priya@example.com", "service": "Root Canal Treatment",
            "preferred_datetime": "next Monday at 3pm", "notes": "sensitive tooth" } }
```
```json
{ "status": "success", "booking_reference": "QDC-5Q1A",
  "confirmed_datetime": "Monday, July 06 at 3:00 PM", "message": "Appointment booked." }
```

---

## 6. Clinic assumptions

Made per the brief's "reasonable assumptions" clause: consultation fee ₹500 (adjusted
against same-day treatment); address 3rd Floor, Baner Business Hub, Baner Road, Pune
411045; walk-ins accepted but appointments preferred; same-day emergency slots during
hours; payment by cash / UPI / cards, most insurance accepted (confirmed at desk).
All of these live in the RetellAI **global prompt** and are trivial to edit.

---

## 7. Testing without live calls

- **Retell dashboard** has a built-in "Test" web call and a webhook/custom-function
  tester — hit *Test* on each tool to send a real payload to your endpoint.
- **Backend locally:** run the app and `curl` the endpoints, or use `/docs` (FastAPI's
  auto Swagger UI) at `http://localhost:8000/docs`.
