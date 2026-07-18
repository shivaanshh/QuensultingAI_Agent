# AI Receptionist Platform

A multi-tenant inbound voice-agent platform, built on **RetellAI Conversational
Flow** with a **FastAPI** automation backend. One shared 14-node conversation
skeleton is parameterized per tenant by a **category template** — dental/medical
clinics, salons & spas, restaurants, and home services (plumbing/electrical/
contracting) ship today. Standing up a new tenant is a CLI command, not
hand-authored JSON or manual dashboard clicks (see [§5.5](#55-onboarding-a-new-tenant)).

**QuensultingAI Dental Clinic** is tenant #1 and the reference implementation —
its category template (`app/templates/dental_medical.py`) was transcribed
verbatim from the original hand-built, live-tested `retell_conversation_flow.json`
kept at the repo root, so it doubles as the parity baseline the other three
categories are checked against.

Each category's agent persona (e.g. "Ava" for dental, "Bella" for salon/spa,
"Leo" for restaurant, "Jordan" for home services) answers calls, handles FAQs,
triages urgent/emergency requests, collects caller details, checks availability
against that tenant's working hours, books the appointment/reservation/service
call, and transfers to a human whenever asked.

---

## 1. Architecture

```
   ┌──────────────┐     voice      ┌──────────────────────────┐
   │   Caller     │ ─────────────▶ │        RetellAI            │
   │  (phone)     │ ◀───────────── │   Conversation Flow        │
   └──────────────┘                │  (one per tenant, built    │
                                   │   from a category template  │
                                   │   at provisioning time)      │
                                   └────────────┬────────────────┘
                                                │ HTTPS (custom tools)
                  check-availability / book-appointment (tenant-scoped URLs)
                                                ▼
                                   ┌──────────────────────────┐
                                   │      FastAPI backend      │
                                   │         (app/)             │
                                   │  resolves {tenant_slug}    │
                                   │  from the URL path          │
                                   └───┬─────────┬─────────┬───┘
                                       │         │         │
                             ┌─────────▼──┐  ┌───▼────┐  ┌─▼───────────────┐
                             │ Tenant DB  │  │ Google │  │  SMTP + optional │
                             │(tenants /  │  │ Sheets │  │  outbound webhook│
                             │ services / │  │(optional│  │  (best-effort)   │
                             │ bookings)  │  │per-tenant)│ │                 │
                             └────────────┘  └─────────┘  └─────────────────┘
```

**Why this shape.** The conversation logic lives entirely in each tenant's
RetellAI graph (nodes + edges), so it's inspectable and versioned in the
dashboard, and structurally identical across every category — only the prose
and a handful of data lists (services, urgent-branch copy, extra slots) vary
per category template. The backend is a thin, stateless, tenant-scoped set of
webhooks — it resolves the tenant from the URL path, validates input, enforces
that tenant's own business rules (working hours, timezone), persists the
record, and notifies. The database write is the hard-fail gate — a booking
isn't "done" until it's saved; Google Sheets, email, and the outbound webhook
are best-effort afterwards and never undo or block a booking.

---

## 2. Conversation flow

This 14-node skeleton (`app/templates/skeleton.py`) is shared, unchanged, by
every tenant in every category — node/edge/tool IDs never vary. Start speaker
is the **agent** (it greets on pickup):

```
                              ┌──────────────┐
                              │ node_welcome │  greet + detect intent
                              └──┬───┬────┬──┘
              books ────────────┘   │    └──────────── urgent/emergency
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
  back verbatim, and corrections loop cleanly back to collection. Category-specific
  extra slots (e.g. `party_size` for restaurants) are appended here too — see
  `extra_slots` in [§4](#4-category-templates).
- **Availability check before confirmation.** The agent never confirms a slot
  outside that tenant's working hours/weekdays; out-of-hours requests route to
  `node_suggest_alt` with concrete alternatives from the backend.
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
├── retell_conversation_flow.json   # Original hand-built dental flow (historical
│                                    # reference + parity baseline; see app/templates/)
├── app/
│   ├── main.py             # FastAPI app: tenant-scoped webhooks + admin API + SPA serving
│   ├── config.py           # platform-only env settings (DB, Retell, SMTP, Sheets)
│   ├── db.py                # SQLAlchemy engine/session (SQLite by default)
│   ├── db_models.py         # Tenant / Service / Booking / CallEvent ORM models
│   ├── tenancy.py           # get_tenant_or_404() — resolves {tenant_slug}
│   ├── bookings.py          # save_booking() + compute_extra_fields()
│   ├── models.py            # pydantic request/response schemas
│   ├── utils.py             # booking refs + working-hours/datetime logic (tenant-parameterized)
│   ├── sheets.py             # optional per-tenant Google Sheets export
│   ├── notifications.py     # SMTP email + optional outbound webhook + contact form
│   ├── flow_builder.py      # build_flow()/validate_flow() -- renders a template for a tenant
│   ├── provisioning.py      # provision_tenant() -- calls the Retell API
│   ├── onboarding.py        # shared tenant-creation validation (CLI + admin API)
│   ├── admin_api.py         # /api/* routes -- tenants, categories, provision, contact
│   ├── portal_api.py        # /api/* routes -- call log, analytics, bookings/services/settings
│   ├── call_events.py       # upsert one CallEvent per call from retell-events webhook
│   ├── admin_schemas.py     # pydantic schemas for the admin + portal APIs
│   └── templates/
│       ├── base.py                # CategoryTemplate dataclass
│       ├── skeleton.py             # the shared 14-node flow skeleton
│       ├── registry.py             # CATEGORY_TEMPLATES + get_template()
│       ├── dental_medical.py       # category #1 (reference/parity baseline)
│       ├── salon_spa.py            # category #2
│       ├── restaurant.py           # category #3
│       └── home_services.py        # category #4
├── frontend/                # React/TS/Vite/Tailwind SPA -- marketing site, client
│   │                         # portal, and admin dashboard (see "Frontend" below)
│   └── src/
│       ├── api/                    # client.ts (fetch wrapper) + types.ts
│       ├── lib/                    # theme (light/dark), motion variants
│       ├── components/layout/      # Public / Admin / Portal shells (+ theme toggle)
│       ├── components/ui/          # shared UI kit + hand-rolled SVG Charts
│       └── pages/                  # public/ (Home/Features/Pricing/About/Contact),
│                                   #   portal/ (Overview/Bookings/Calls/Services/Settings),
│                                   #   admin/ (TenantsList/NewTenantWizard/TenantDetail)
├── scripts/
│   ├── create_tenant.py       # onboard/provision any tenant, any category (see §5.5)
│   └── seed_dental_tenant.py  # idempotent: (re)inserts the dental reference tenant
├── data/                    # SQLite file lives here (gitignored)
├── tests/                   # pytest suite (80 tests, no external services hit)
│   ├── test_utils.py
│   ├── test_api.py
│   ├── test_db_models.py
│   ├── test_flow_builder.py
│   ├── test_provisioning.py
│   ├── test_admin_api.py
│   └── test_portal_api.py
├── n8n_workflow.json      # alternative single-tenant booking automation (importable n8n)
├── Dockerfile             # multi-stage: builds frontend/, then serves it from the API image
├── .dockerignore
├── render.yaml            # one-click Render.com Blueprint deploy (Docker runtime)
├── Procfile               # Railway / Heroku-style deploy
├── requirements.txt
├── requirements-dev.txt   # requirements + pytest
├── .env.example
├── SUBMISSION.md          # original single-tenant deliverables checklist
├── RUN_LOCAL.md           # local + ngrok quick-demo walkthrough
├── N8N_SETUP.md           # how to import/configure the n8n workflow
├── LOOM_SCRIPT.md         # walkthrough script for the recording
└── README.md
```

> **Automation: two options.** The primary automation is the Python/FastAPI backend in
> `app/` — it's tenant-aware, does the availability logic, and has tests. `n8n_workflow.json`
> is an older, single-tenant alternative for just the booking step (webhook → Google Sheets
> → email); see `N8N_SETUP.md`. New tenants should use the FastAPI backend.

### Run the tests

```bash
pip install -r requirements-dev.txt
pytest -q          # 80 passing; stubs Sheets/email, hits no external services
```

### Deploy to the cloud (so Retell can reach it)

The backend needs a public HTTPS URL. Three options:

- **Render** — push this repo, create a *Blueprint* from `render.yaml`, and fill in the
  secret env vars. Paste your whole service-account key into `GOOGLE_CREDENTIALS_JSON`.
  `startCommand` re-runs `scripts/seed_dental_tenant.py` on every boot so the dental
  reference tenant always exists, even on the free tier's ephemeral disk.
- **Railway / Fly / Heroku** — the `Procfile` works as-is; set the same env vars.
- **Docker** — `docker build -t receptionist . && docker run -p 8000:8000 --env-file .env receptionist`.
- **Local + ngrok** — for a quick demo: `uvicorn app.main:app` then `ngrok http 8000`.

> On cloud hosts you usually can't upload the `google-credentials.json` file. Use
> `GOOGLE_CREDENTIALS_JSON` instead — paste the entire key JSON into that one env var.
>
> On Render's free plan, the disk is ephemeral — every redeploy starts from a fresh
> SQLite file, so booking history is lost on redeploy until `DATABASE_URL` points at a
> real Postgres instance (a config change only, no code change needed).

### Frontend (marketing site + client portal + admin dashboard)

`frontend/` is a React + TypeScript + Vite + Tailwind CSS single-page app,
light/dark themed, with three independent route trees:

- **Marketing site** (`/`, `/features`, `/pricing`, `/about`, `/contact`) —
  public. Home shows the live category grid, Features tours the product and
  links to a live demo dashboard, Pricing lists plan tiers, and Contact posts to
  `POST /api/contact`.
- **Client portal** (`/portal`, `/portal/:slug/...`) — the business-owner
  dashboard. A business is picked at `/portal`, then a five-page app-shell:
  **Overview** (call/booking trend charts, answer rate, caller sentiment),
  **Bookings** (search/filter + mark completed/cancelled), **Calls** (call log
  with duration, outcome, sentiment, transcript), **Services** (add/price/toggle),
  and **Settings** (hours, transfer number, notifications, pause the agent).
  Charts are hand-rolled SVG — no chart library.
- **Admin dashboard** (`/admin`, `/admin/new`, `/admin/tenants/:slug`) — tenant
  list, a new-tenant wizard, and a tenant detail page (business info, services,
  recent bookings, a friendly render of the provisioning preview, and a
  Provision/Re-provision button). It's a UI on top of the same
  `app/onboarding.py` + `app/flow_builder.py` + `app/provisioning.py` functions
  `scripts/create_tenant.py` already uses — not a separate implementation.

The portal's call log and analytics are backed by **real data**: the
`/webhook/{slug}/retell-events` handler now persists one `CallEvent` per call
(upserted across the call_started → call_ended → call_analyzed lifecycle), so the
dashboard only ever shows calls that actually happened — nothing synthetic. Until
the agent's Webhook URL is configured in Retell and calls come in, the portal
shows empty states.

> **⚠️ No authentication.** Both the `/admin` console and the `/portal` client
> dashboard ship with zero auth in this build — anyone who knows (or guesses) a
> URL can view a business's data, edit its settings, and (on `/admin`) trigger
> real, billed Retell provisioning. Don't put these URLs on a memorable domain,
> don't link them from the public site, and don't share them outside the team
> until real auth is added. API responses never include `webhook_secret`, but
> that's the only secret-leak protection in place.

**Dev workflow** — run the backend and the Vite dev server side by side; Vite
proxies `/api` and `/health` to `uvicorn` on port 8000, so the frontend always
calls relative paths (no CORS setup, no build-time API base URL):

```bash
uvicorn app.main:app --reload          # terminal 1 -- backend on :8000
cd frontend && npm install && npm run dev   # terminal 2 -- Vite on its own port
```

**Production build** — `npm run build` emits static files to `frontend/dist`,
which `app/main.py` serves same-origin (mounted at `/assets`, with a catch-all
SPA fallback for client routes like `/admin/tenants/glow-salon`). This happens
automatically in the Docker image (see below); to build it locally:

```bash
cd frontend && npm run build
```

If `frontend/dist` doesn't exist (e.g. a backend-only checkout), `/` and
`/admin/*` simply 404 — the API and webhook routes are unaffected.

---

## 4. Category templates

| Category key | Display name | Persona | Booking noun | Extra slots |
|---|---|---|---|---|
| `dental_medical` | Dental / Medical Clinic | Ava | appointment | — |
| `salon_spa` | Salon & Spa | Bella | appointment | `stylist_preference` |
| `restaurant` | Restaurant | Leo | reservation | `party_size` (required), `occasion` |
| `home_services` | Home Services (Plumbing/Electrical/Contracting) | Jordan | service call | `urgency_level`, `property_type` |

Each template (`app/templates/<category>.py`) is a `CategoryTemplate` dataclass:
persona name/role sentence, customer/service/staff nouns, an urgent-branch copy
block (emergency triage for dental, urgent dispatch for home services, large-party/
allergy escalation for restaurants, adverse-reaction/urgent-booking for salon/spa),
default starter services, FAQ fact-bullet labels, and an optional `extra_slots` list.
`extra_slots` are appended to both the `extract_dynamic_variables` node and the
`book_appointment` tool's parameters with zero backend code changes — any tool
argument that isn't one of the fixed booking columns automatically lands in
`Booking.extra_fields` (a JSON column) via `app/bookings.py`'s `compute_extra_fields()`.

Adding a **5th category** is: write a new `app/templates/<key>.py` following the
existing four as examples, register it in `app/templates/registry.py`'s
`CATEGORY_TEMPLATES` dict, verify `default_voice_id` against a live
`GET /list-voices` call (see the note in `app/provisioning.py`), and it's
immediately usable via `scripts/create_tenant.py --category <key>` — no other
code changes needed.

---

## 5. Setup

### 5.1 Backend

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then fill in the values (see below)
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The SQLite database (`DATABASE_URL`, default `sqlite:///./data/tenants.db`) and
its tables are created automatically on startup — no separate migration step
for v1 (plain `Base.metadata.create_all()`; Alembic is a deferred polish item).

Expose it publicly so Retell can reach it. During development:

```bash
ngrok http 8000               # gives you https://<subdomain>.ngrok-free.app
```

Set `BACKEND_BASE_URL` in `.env` to that public URL — it's used to build every
tenant's tool webhook URLs at provisioning time (see §5.5).

Health check: `GET https://<your-host>/health`.

### 5.2 Google Sheets (optional, per tenant)

Sheets export is opt-in per tenant: leave a tenant's `google_sheets_id` blank
and `append_booking()` is a no-op for that tenant.

1. In Google Cloud, create a **service account** and download its JSON key as
   `google-credentials.json` (place it in the project root), or paste the whole
   key JSON into `GOOGLE_CREDENTIALS_JSON` (needed on hosts that can't hold an
   uploaded file, e.g. Render).
2. Enable the **Google Sheets API** for that project.
3. Create a Google Sheet and **share it (Editor)** with the service account email
   (`...@....iam.gserviceaccount.com`).
4. Put the sheet ID (from its URL) into that tenant's `google_sheets_id` (pass
   `--google-sheets-id` to `scripts/create_tenant.py`, or edit the row directly).

The `Bookings` worksheet and header row are created automatically on first write.

### 5.3 Email (SMTP)

One shared sending identity for every tenant in v1 (per-tenant verified senders
are a deferred polish item). For Gmail: turn on 2-factor auth, create an **App
Password**, and use it as `SMTP_PASSWORD`. Any SMTP provider (SendGrid, SES,
Mailgun) works by changing `SMTP_HOST`/`SMTP_PORT`/credentials. Leave these
blank and email is simply skipped.

### 5.4 RetellAI provisioning credentials

Set in `.env`:

- `RETELL_API_KEY` — from the Retell dashboard (Settings → API Keys). Treat it
  as a secret: it's only ever read from the environment, never logged or
  committed.
- `RETELL_API_BASE` — defaults to `https://api.retellai.com`; only change it
  if Retell gives you a different endpoint.
- `BACKEND_BASE_URL` — the public HTTPS URL from §5.1; every tenant's tool
  URLs are built as `{BACKEND_BASE_URL}/webhook/{tenant_slug}/...`.

### 5.5 Onboarding a new tenant

`scripts/create_tenant.py` is the scriptable onboarding path (the `/admin`
dashboard — see [Frontend](#frontend-marketing-site--admin-dashboard) — is a
UI on top of the same underlying functions, for anyone who'd rather click
through a form). It builds and validates that tenant's flow from a category
template, then (unless `--dry-run`) calls the Retell API to create a **new,
independent** conversation flow + agent for it.

**1. See what categories exist:**

```bash
python scripts/create_tenant.py --list-categories
```

**2. Dry-run a new tenant** — prints the fully rendered flow JSON, touches
neither the database nor the Retell API. Always do this first and read the
output (global prompt, service list, urgent-branch copy) before spending a
real API call:

```bash
python scripts/create_tenant.py \
  --slug glow-salon --category salon_spa \
  --business-name "Glow Salon & Spa" \
  --address "12 MG Road, Pune" \
  --timezone Asia/Kolkata --open-hour 10 --close-hour 20 \
  --open-weekdays 0,1,2,3,4,5 \
  --transfer-number "+919000000001" \
  --notification-email "owner@glowsalon.example" \
  --service "Haircut & Styling" --service "Manicure & Pedicure" \
  --dry-run
```

`--slug` must be URL-safe (lowercase letters, digits, hyphens — it becomes
part of the webhook URL path). Omit `--service` to fall back to that
category's default starter service list.

**3. Provision for real** — same command, minus `--dry-run`. This inserts the
tenant row (with a freshly generated per-tenant `webhook_secret`), then calls
`create-conversation-flow` and `create-agent` on the live Retell API and
persists the returned `retell_conversation_flow_id`/`retell_agent_id` back
onto the tenant:

```bash
python scripts/create_tenant.py \
  --slug glow-salon --category salon_spa \
  --business-name "Glow Salon & Spa" --address "12 MG Road, Pune" \
  --service "Haircut & Styling" --service "Manicure & Pedicure"
```

```
Created tenant 'glow-salon' (category=salon_spa).
Provisioned tenant 'glow-salon':
  conversation_flow_id = conversation_flow_xxxxxxxx
  agent_id             = agent_xxxxxxxx
```

If a tenant already has a `retell_agent_id`, the script refuses to
re-provision it (protects against accidentally creating duplicate live
agents) unless you pass `--reprovision` — which still creates a **new**,
independent agent/flow side-by-side, since Retell's update endpoints aren't
exercised by this codebase.

**4. Manual dashboard steps** (not automatable — do these once per tenant in
the Retell dashboard):

- Open the new agent, confirm the voice and the two custom tools' URLs look
  right (`https://<your-host>/webhook/glow-salon/check-availability?token=...`
  and `.../book-appointment?token=...`).
- Attach a phone number and publish.
- (Optional) set the agent-level **Webhook URL** to
  `https://<your-host>/webhook/glow-salon/retell-events` to log call events.

**5. Smoke-test** — place a real call to the attached number and confirm the
FAQ, urgent-branch, and booking paths all behave as expected for that
category, the way the dental reference tenant was verified live in this repo's
history.

**Existing tenant, e.g. re-running the reference dental tenant:**

```bash
python scripts/create_tenant.py --slug quensulting-dental --dry-run
```

(`scripts/seed_dental_tenant.py` is the one-time/idempotent migration that
originally inserted `quensulting-dental` with its real production facts —
most new tenants should use `create_tenant.py` directly instead.)

---

## 6. API reference

**RetellAI webhooks** (tenant-scoped, protected by `?token={webhook_secret}`):

| Method | Path | Purpose |
|---|---|---|
| GET  | `/health` | Liveness check |
| POST | `/webhook/{tenant_slug}/check-availability` | Custom tool — returns `{available, reason, suggested_slots}` |
| POST | `/webhook/{tenant_slug}/book-appointment` | Custom tool — persists + notifies, returns `{status, booking_reference, confirmed_datetime}` |
| POST | `/webhook/{tenant_slug}/retell-events` | Optional agent webhook — upserts a `CallEvent` per call (`call_started/ended/analyzed`) |

Both tool endpoints accept Retell's `{ "call": {...}, "args": {...} }` envelope and
also a flat body (`args_at_root=true`). They're protected by that tenant's own
`webhook_secret`, passed as `?token=`.

**Frontend API** (`/api/*`, consumed by the SPA; **no auth** — never returns
`webhook_secret`):

| Method | Path | Purpose |
|---|---|---|
| GET  | `/api/categories` | The 4 category templates (for the wizard + marketing grid) |
| GET/POST | `/api/tenants` | List tenants / create a tenant (unprovisioned) |
| GET  | `/api/tenants/{slug}` | Detail + services + recent bookings |
| GET  | `/api/tenants/{slug}/preview` | `build_flow()` output for review |
| POST | `/api/tenants/{slug}/provision` | Provision on Retell (`?reprovision=true` to force) |
| POST | `/api/contact` | Marketing contact form → SMTP |
| GET  | `/api/tenants/{slug}/calls` | Call log (most recent first) |
| GET  | `/api/tenants/{slug}/analytics?days=` | Aggregates: calls/bookings per day, sentiment, top services, conversion |
| PATCH | `/api/tenants/{slug}/bookings/{id}` | Update booking status (confirmed/completed/cancelled/no_show) |
| GET/POST | `/api/tenants/{slug}/services` | List / add a service |
| PATCH/DELETE | `/api/tenants/{slug}/services/{id}` | Edit·toggle / remove a service |
| PATCH | `/api/tenants/{slug}/settings` | Update hours, transfer number, notifications, status |

### Example (what Retell sends → what it gets back)

```jsonc
// POST /webhook/quensulting-dental/book-appointment?token=...
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

A restaurant tenant's `book_appointment` call carries the same fixed args plus
its `extra_slots` (e.g. `party_size`, `occasion`), which land in that
booking's `extra_fields` JSON column automatically — no endpoint changes
needed per category.

---

## 7. QuensultingAI Dental Clinic (reference tenant) — assumptions

Made per the original brief's "reasonable assumptions" clause: consultation fee
₹500 (adjusted against same-day treatment); address 3rd Floor, Baner Business
Hub, Baner Road, Pune 411045; walk-ins accepted but appointments preferred;
same-day emergency slots during hours; payment by cash / UPI / cards, most
insurance accepted (confirmed at desk). All of these live in the tenant row's
`extra_facts` / `address` / etc. (see `scripts/seed_dental_tenant.py`) and flow
into the RetellAI **global prompt** via the category template — edit the
database row, not code, to change them.

---

## 8. Testing without live calls

- **Retell dashboard** has a built-in "Test" web call and a webhook/custom-function
  tester — hit *Test* on each tool to send a real payload to your endpoint.
- **Backend locally:** run the app and `curl` the endpoints, or use `/docs` (FastAPI's
  auto Swagger UI) at `http://localhost:8000/docs`.
- **`scripts/create_tenant.py --dry-run`** renders and structurally validates a
  tenant's flow without touching the database or the Retell API — the fastest
  way to review a new category or a copy change before spending a real API call.
- **`pytest -q`** — 50 hermetic tests: booking-reference/working-hours/datetime
  logic, the tenant-scoped API routes (in-memory SQLite), every registered
  category template builds and validates against the shared skeleton, and
  provisioning against a mocked Retell API (`httpx.MockTransport` — no test
  ever hits the real Retell API).

---

## 9. Explicitly out of scope (deferred, not silently dropped)

Admin web UI, billing/subscriptions, automated phone-number purchasing/porting
(stays a manual Retell dashboard step per tenant), Alembic migrations,
per-tenant SMTP sending identity, rate limiting, and — worth flagging since
dental/medical is a launch category — any HIPAA-adjacent compliance work for
health data.
