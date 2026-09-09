# Kagutsuchi Dashboard (鍛・検証)

The real-time web dashboard for Kagutsuchi's verification runs. Reads a
Postgres database of actual pipeline results — it does not generate or
display any sample/fake data. Empty until the first real run is
published via `integration/publish_result.py` (see repo root).

## Stack

- Next.js 16 (App Router) + TypeScript + Tailwind CSS v4
- Neon Postgres (via Vercel's Postgres storage integration)
- No ORM — plain SQL via `@neondatabase/serverless`, schema created
  automatically on first request (see `lib/db.ts`'s `ensureSchema()`)

## Deploying (one-time setup)

1. **Import this repo into Vercel.** On vercel.com, "Add New" → "Project"
   → import `Project-KAGUTSUCHI` from GitHub → set **Root Directory** to
   `webapp` (this is a monorepo — the Next.js app lives in this
   subfolder, not the repo root).
2. **Add a Postgres database.** In the new Vercel project: Storage tab →
   "Connect Store" → Postgres (Neon) → create a new database. This
   automatically sets the `DATABASE_URL` environment variable — no manual
   connection string needed.
3. **Set `INGEST_API_KEY`.** Project Settings → Environment Variables →
   add `INGEST_API_KEY` with any random string as the value (this is the
   shared secret that authorizes `publish_result.py` to write new runs).
4. **Deploy.** Vercel deploys automatically on every push to `main` once
   connected — no further action needed after step 3.
5. **Publish a real run.** From the repo root (needs a reachable Docker
   daemon — see `integration/demo.py`):
   ```
   export DASHBOARD_URL=https://<your-project>.vercel.app
   export DASHBOARD_API_KEY=<the same value as INGEST_API_KEY>
   PYTHONPATH=. python -m integration.publish_result demo
   PYTHONPATH=. python -m integration.publish_result demo_sql
   ```
   Reload the dashboard — the run(s) should now appear.

## Local development

```
npm install
cp .env.example .env.local   # fill in DATABASE_URL + INGEST_API_KEY
npm run dev
```

Without a real `DATABASE_URL`, the app will error when a page actually
queries the database (by design — see `lib/db.ts`) rather than silently
falling back to fake data.
