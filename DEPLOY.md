# Deploy & go-live checklist

Everything below is operational — code is done. Work top to bottom.

> ⚠️ **No authentication yet.** `/admin` and `/portal` are open to anyone with the
> URL. Don't attach a memorable custom domain or share the links publicly until
> an auth layer is added.

---

## 1. (Recommended) Local Docker smoke test

The repo switched to `runtime: docker`, but the image has **not** been built or
run locally yet (Docker wasn't available on the dev machine). Do this once before
the first cloud deploy so a broken build doesn't surprise you on Render.

```bash
docker build -t quensulting .
docker run --rm -p 8000:8000 --env-file .env quensulting
```

Then, in another terminal, confirm the three surfaces respond:

```bash
curl -s -o NUL -w "%{http_code}\n" http://localhost:8000/health          # 200
curl -s -o NUL -w "%{http_code}\n" http://localhost:8000/                 # 200 (frontend)
curl -s -o NUL -w "%{http_code}\n" http://localhost:8000/api/tenants      # 200 (JSON)
```

The image is multi-stage: Node builds `frontend/` → the Python image serves it,
and `CMD` runs `scripts/seed_dental_tenant.py` before uvicorn, so the dental
reference tenant always exists on boot.

---

## 2. Deploy to Render

1. Push to GitHub (see the commit/push commands in the chat / README).
2. In Render: **New → Blueprint**, point it at this repo. It reads `render.yaml`
   (`runtime: docker`).
3. Fill in the secret env vars (marked `sync: false`):
   - `RETELL_API_KEY` — your Retell key (**rotate first**, see §5).
   - `BACKEND_BASE_URL` — set to this service's own Render URL, e.g.
     `https://quensulting-dental-voice-agent.onrender.com`. Provisioning bakes
     this into every tenant's webhook tool URLs, so it must be correct.
   - `GOOGLE_CREDENTIALS_JSON` — paste the whole service-account key (optional;
     only if a tenant uses Sheets export).
   - `SMTP_USER`, `SMTP_PASSWORD`, `FROM_EMAIL` — for confirmation + contact-form
     email (optional but recommended).
4. **Watch the first build.** It's a two-stage build (npm install + Vite build +
   pip install) on the free tier — keep an eye on build-minute / memory limits.
5. Free plan has an **ephemeral disk**: every redeploy resets the SQLite file, so
   booking/call history is lost on redeploy. When you have a real paying tenant,
   add a `DATABASE_URL` env var pointing at a Postgres instance (config change
   only, no code change).

---

## 3. Populate a demo (optional, for showing the dashboard)

The `/portal` dashboard is empty until real calls arrive. To showcase it with
realistic sample data on a clearly-labelled **demo** tenant:

```bash
python scripts/seed_demo_data.py         # creates demo-glow-salon with sample calls + bookings
```

The Features page's "see a live dashboard" button links to `/portal/demo-glow-salon`.

---

## 4. Take one tenant live (real call — manual, billed)

These steps hit the **real, billed** Retell API and can't be automated end-to-end.

1. Onboard the tenant (CLI or the `/admin` wizard). Do a `--dry-run` first.
2. **Provision** it (`/admin/tenants/<slug>` → "Provision on Retell", or
   `python scripts/create_tenant.py ... ` without `--dry-run`). This creates a
   real agent + conversation flow and persists their ids.
3. In the Retell dashboard for that agent:
   - Confirm the two custom tools' URLs are
     `https://<render-url>/webhook/<slug>/check-availability?token=...` and
     `.../book-appointment?token=...`.
   - **Attach a phone number** and publish.
   - Set the agent-level **Webhook URL** to
     `https://<render-url>/webhook/<slug>/retell-events` — this is what feeds the
     portal's call log + analytics.
4. **Place a real call.** Confirm:
   - The FAQ, urgent-branch, and booking paths behave for that category.
   - A booking row appears (`/portal/<slug>/bookings`).
   - The call appears with transcript/sentiment (`/portal/<slug>/calls`) and the
     Overview charts move. *(This portal → real-Retell path has only ever been
     exercised with tests + seeded data, so this is the first true end-to-end
     confirmation.)*

---

## 5. Rotate the Retell API key

The key was pasted into a chat transcript earlier, so treat it as compromised:

1. Retell dashboard → API keys → **revoke the old key, create a new one**.
2. Update it in **two** places: the `RETELL_API_KEY` env var on Render, and your
   local `.env` (which is gitignored and never committed).
3. No code change needed — the app reads it from the environment.
