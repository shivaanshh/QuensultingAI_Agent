# Loom Walkthrough Script (3–5 min)

A tight script so the recording stays inside the time limit. Practice once; the
timings are a guide. Have three tabs open: (1) Retell flow canvas, (2) your code
editor, (3) the Google Sheet.

---

## 0:00 – 0:25 · Intro
> "Hi, I'm [Name]. This is my AI receptionist voice agent for QuensultingAI Dental
> Clinic. It's built on RetellAI's Conversational Flow, with a FastAPI backend that
> saves bookings to Google Sheets and sends a confirmation email. Let me walk through
> the conversation design, the automation, and the integrations."

## 0:25 – 1:45 · Conversation flow (share the Retell canvas)
> "The agent greets the caller and the welcome node only classifies intent — book,
> a question, or an emergency — then branches. I kept each node single-purpose."

Point at the graph as you talk:
- **FAQ node** answers timings, location, fee, services, payment — from the global prompt.
- **Emergency node** shows empathy and offers an immediate transfer.
- **Collect details** gathers name, phone, email, service, and time — one question at a
  time, reading the number back.
- **Extract node** pins those to dynamic variables.
- **Check availability** is a function call to my backend. "Notice this branch uses an
  *equation* edge — `slot_available == true` — so it's driven by real data, not a guess.
  Out-of-hours requests go to *suggest alternative*."
- **Confirm** reads everything back; **Book** calls the backend; then **success** or a
  **failure fallback**.
- "And this transfer node is a **global node** — so 'let me talk to a person' works from
  anywhere in the call. That's the escalation requirement."

## 1:45 – 3:15 · Automation & integrations (share the editor)
> "The backend is FastAPI — three webhooks." Open `app/main.py`.
- `check-availability`: "parses the spoken time and checks it against Mon–Sat 9-to-6."
  Show `utils.within_working_hours`.
- `book-appointment`: "validates required fields, generates a reference, then does three
  things." Scroll to the three steps.
  1. `append_booking` → **Google Sheets** (source of truth). Flip to the sheet tab and
     show a row landing.
  2. `send_confirmation_email` → **SMTP confirmation email**. Show the email.
  3. `fire_booking_webhook` → optional outbound webhook.
- "Notifications are best-effort — if email fails, the booking still succeeds, because
  the record is already saved."

## 3:15 – 4:15 · Live demo (Retell test call)
> "Here's a quick test call." Run the dashboard test call:
- Ask "what are your timings?" → FAQ answers.
- "I'd like to book a cleaning next Monday at 3pm." → collect → availability → confirm → book.
- Show the booking reference spoken back, the new Google Sheet row, and the email.
- Optionally: "Can I speak to someone?" mid-call → global transfer fires.

## 4:15 – 4:45 · Design decisions & close
> "Three decisions I'd highlight: one, all conversation logic lives in the graph so it's
> inspectable and versioned; two, deterministic equation edges for anything backed by
> data; three, real fallback nodes for booking and transfer failures instead of dead
> ends. Google Sheets is the single source of truth and notifications never block a
> booking. Thanks for watching."

---

### Recording tips
- Record at 1080p, keep it under 5 minutes.
- Set the tool URLs and a real transfer number *before* recording so the demo works.
- If a live call is flaky, fall back to the Retell web-call test + the webhook tester.
- **Make the Loom link 'anyone with the link can view'** (the brief requires public links).
