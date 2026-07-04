# n8n Workflow — alternative booking automation

`n8n_workflow.json` is an **importable n8n workflow** that does the same booking
automation as the FastAPI backend: it receives the Retell `book_appointment` call,
appends the record to **Google Sheets**, responds to Retell with a booking reference,
and sends a **confirmation email**. It's provided as a second automation option — the
brief asks for *n8n **or** Python*, and this shows both.

```
Webhook ──▶ Build Booking Record ──▶ Save to Google Sheet ──▶ Respond to Retell ──▶ Send Confirmation Email
(POST)      (Code: ref + fields)      (append row)             (JSON back to agent)   (best-effort, after reply)
```

Note the order: the workflow **responds to Retell right after the row is saved**, then
sends the email. So a slow or failing email never delays the caller — the same
"Sheets is the source of truth, email is best-effort" design as the Python backend
(`onError: continueRegularOutput` on the email node makes an email failure non-fatal).

## Import & configure

1. **Import** — in n8n: *Workflows → Import from File →* `n8n_workflow.json`.
2. **Google Sheets node** ("Save to Google Sheet"):
   - Set/select a **Google Sheets credential** (OAuth2 or a service account).
   - Replace `YOUR_GOOGLE_SHEET_ID` with your sheet's ID.
   - Make sure the sheet's first tab is named **Bookings** with this header row:
     `Timestamp | Booking Reference | Patient Name | Phone | Email | Service | Preferred Time | Confirmed Time | Notes | Call ID | Status`
3. **Send Confirmation Email node**:
   - Set an **SMTP credential** (for Gmail: an App Password).
   - Change `fromEmail` to your clinic address.
4. **Activate** the workflow (toggle top-right). Copy the **Production webhook URL**
   from the Webhook node (looks like `https://<your-n8n>/webhook/book-appointment`).
5. **Point Retell at it** — in the imported Retell agent, open the `book_appointment`
   tool and set its URL to that n8n production webhook URL (instead of the FastAPI one).

## Which automation should I use?

- **Python/FastAPI** (`app/`) is the primary implementation — it also does the
  `check_availability` working-hours logic and ships with tests.
- **n8n** (`n8n_workflow.json`) is the alternative for the **booking** step. If you use
  n8n for booking, keep `check_availability` pointed at the FastAPI backend (the
  Mon–Sat 9–6 parsing lives there), or remove that node from the flow.

Use one or the other for the `book_appointment` tool URL — not both at once.
