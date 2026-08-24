# Deployment notes (PLANNING.md Section C.1)

**Independent proof of concept — not affiliated with PakWheels.**

Do not deploy until local README setup works cleanly.

## Frontend — Vercel

1. Root directory: `frontend`
2. Framework preset: Next.js
3. Environment variable:
   - `NEXT_PUBLIC_API_URL` = public HTTPS URL of the backend (no trailing slash)
4. Build: `npm run build` · Output: Next default

## Backend — Render / Railway

1. Dockerfile path: `backend/Dockerfile` (or native Python + `uvicorn`)
2. Required env vars (see `backend/.env.example`):
   - `DATABASE_URL` (managed Postgres; enable **pgvector**)
   - `CORS_ORIGINS` (your Vercel URL)
   - `AI_PROVIDER`, provider API key + model
   - `EMBEDDING_MODEL`, `RATE_LIMIT_PER_MINUTE`, `CONVERSATION_RETENTION_DAYS`
   - `DEBUG=false` in production
3. Release / one-off commands:
   - `alembic upgrade head`
   - `python -m app.scripts.seed_vehicles` (demo only)
   - `python -m app.scripts.ingest_knowledge`
4. Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Schedule retention: `python -m app.scripts.purge_old_conversations`

## Docker Compose (local)

```bash
# Set OPENROUTER_API_KEY in the environment, then:
docker compose up --build db api
```

Run the frontend separately with `NEXT_PUBLIC_API_URL=http://localhost:8000`.

## Checklist before first deploy

- [ ] Fresh clone follows README without undocumented steps  
- [ ] `.env` / `.env.local` gitignored; examples up to date  
- [ ] `/health` OK; `/docs` lists all routes  
- [ ] Extract / recommend / compare / analyze / knowledge ask return friendly errors on failure  
- [ ] Disclaimer visible in UI footer  
