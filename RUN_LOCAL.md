# Run locally + expose with ngrok (quick demo for the Loom)

Fastest path to a working end-to-end demo you can record today. ~20–30 min the first
time (most of it is the one-time Google/Gmail setup). Commands are for **Windows**.

---

## Step 1 — Google Sheet + service account (~10 min)

1. Go to <https://console.cloud.google.com/> → create a project (any name).
2. **APIs & Services → Library →** enable **Google Sheets API**.
3. **APIs & Services → Credentials → Create Credentials → Service account.** Name it,
   create, then open it → **Keys → Add key → Create new key → JSON.** A `.json` file
   downloads. Rename it to **`google-credentials.json`** and put it in the project root
   (it's already gitignored, so it won't be pushed).
4. Open the JSON, copy the `client_email` value (looks like
   `...@...iam.gserviceaccount.com`).
5. Create a Google Sheet named e.g. "Dental Bookings". Click **Share**, paste that
   service-account email, give it **Editor**, send.
6. Copy the sheet **ID** from its URL:
   `docs.google.com/spreadsheets/d/`**`THIS_LONG_ID`**`/edit`.

The `Bookings` tab + header row are created automatically on the first booking.

## Step 2 — Gmail App Password (~3 min)

1. Enable **2-Step Verification** on your Google account (required for App Passwords).
2. Go to <https://myaccount.google.com/apppasswords> → create one named "dental" →
   copy the 16-character password (no spaces).

## Step 3 — Configure `.env`

In the project root:

```cmd
copy .env.example .env
```

Open `.env` and set:

```ini
WEBHOOK_SECRET=pick-any-long-random-string
GOOGLE_SHEETS_ID=THE_ID_FROM_STEP_1
GOOGLE_CREDENTIALS_FILE=google-credentials.json
SMTP_USER=your-gmail@gmail.com
SMTP_PASSWORD=your-16-char-app-password
FROM_EMAIL=your-gmail@gmail.com
CLINIC_INBOX=your-gmail@gmail.com
```

## Step 4 — Run the backend

```cmd
cd /d "c:\Users\kaush\OneDrive\Desktop\Projects\quensulting-dental-voice-agent"
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Leave it running. Check <http://localhost:8000/health> in a browser — you should see
`{"status":"ok",...}`.

## Step 5 — Expose it with ngrok

Install from <https://ngrok.com/download> (free; sign up once and run
`ngrok config add-authtoken <token>`), then in a **second** terminal:

```cmd
ngrok http 8000
```

Copy the HTTPS forwarding URL it prints, e.g. `https://ab12cd34.ngrok-free.app`.
Keep this terminal open too (a free ngrok URL changes each restart).

## Step 6 — Wire the Retell agent

1. In the Retell dashboard: **Create Agent → Conversation Flow → Import** →
   `retell_conversation_flow.json`.
2. Open the two custom tools and set their URLs to your ngrok host **with the token**:
   - `check_availability` → `https://<ngrok>.ngrok-free.app/webhook/check-availability?token=<WEBHOOK_SECRET>`
   - `book_appointment` → `https://<ngrok>.ngrok-free.app/webhook/book-appointment?token=<WEBHOOK_SECRET>`
3. Set `node_transfer`'s number (the `{{human_agent_number}}` default) to any real
   number you can pick up for the transfer demo. Pick a voice. Publish.

## Step 7 — Test call (this is your Loom demo)

Use Retell's **Test** (web call) button and run through:

- "What are your timings?" → FAQ answers from the flow.
- "I'd like to book a cleaning **the day after tomorrow at 2pm**." → it collects your
  name/phone/email, checks availability, reads back, and books.
- Watch a **row appear in the Google Sheet** and a **confirmation email** arrive.
- Optionally mid-call: "Can I talk to a person?" → the global transfer node fires.

> Tip: use "day after tomorrow" or a weekday like "next Monday" in the demo — those land
> inside Mon–Sat 9–6. "Tomorrow" may hit a Sunday depending on the day you record.

If a tool call fails, check the uvicorn terminal logs and the ngrok request inspector
(<http://127.0.0.1:4040>) to see the exact request/response.

---

Once this works, record the Loom with `LOOM_SCRIPT.md`, set the link to
"anyone with the link can view", and you're ready to submit (`SUBMISSION.md`).
