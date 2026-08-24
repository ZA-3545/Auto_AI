# Deployment checklist (PLANNING.md Section C.1)

**Independent proof of concept — not affiliated with PakWheels.**

This guide is for **manual** deploy steps only. The repo is deployment-ready; do not
deploy until local README setup works cleanly. Nothing here creates cloud accounts
for you.

## Architecture

| Piece | Platform | Config in repo |
|---|---|---|
| Frontend | Vercel | `frontend/` (Next.js — no `vercel.json` required) |
| Backend | Render **or** Railway | `backend/Dockerfile`, `render.yaml`, `railway.toml` / `railway.json` |
| Database | Managed PostgreSQL with **pgvector** | Set `DATABASE_URL` only |

---

## 0. Before you start

- [ ] Local stack works (`/health`, chat, recommend, compare)
- [ ] Secrets only in platform dashboards — never commit `.env` / `.env.local`
- [ ] Choose **one** backend host: Render **or** Railway

---

## 1. Managed PostgreSQL

1. Create a Postgres instance that supports **pgvector** (e.g. Render Postgres, Railway Postgres, Neon, Supabase, or any host with the extension available).
2. Copy the connection string → you will set it as `DATABASE_URL`.
3. If the provider requires TLS, append `?sslmode=require` (or use their SSL URL).
4. In the provider SQL console (once), ensure the extension exists:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

> Alembic revision `0003_knowledge_chunks` also runs `CREATE EXTENSION IF NOT EXISTS vector` during `alembic upgrade head`. Running the SQL once up front avoids extension/permission surprises on locked-down hosts.

---

## 2. Backend (Render **or** Railway)

### Common

1. Connect the GitHub repo to the platform.
2. Build with Docker:
   - Dockerfile: `backend/Dockerfile`
   - Context: `backend/` (Render Blueprint uses `rootDir: backend`; Railway configs point at `backend/Dockerfile`)
3. Set environment variables in the dashboard (see **Production env vars** below).
4. Confirm the service listens on `$PORT` (the image CMD already does).
5. Health check path: `/health`

### Render

- Optional Blueprint: root `render.yaml` (creates the web service skeleton; fill secrets in the dashboard).
- Or: New Web Service → Docker → root directory `backend`.

### Railway

- Optional: root `railway.toml` / `railway.json` (Dockerfile path `backend/Dockerfile`).
- Or: New service → Dockerfile → set path to `backend/Dockerfile`.

### One-off commands (platform shell / console)

Run **after** `DATABASE_URL` (and AI keys for ingest) are set, from the app working directory (`/app` in the container):

```bash
alembic upgrade head
python -m app.scripts.seed_vehicles --clear
python -m app.scripts.ingest_knowledge
```

Optional retention job (schedule or run periodically):

```bash
python -m app.scripts.purge_old_conversations
```

These scripts use only `DATABASE_URL` (and AI keys for embeddings) from the environment — no localhost paths.

---

## 3. Frontend (Vercel)

1. Import the GitHub repo in Vercel.
2. **Root Directory:** `frontend`
3. Framework preset: Next.js (default build `npm run build` / output).
4. Environment variable:
   - `NEXT_PUBLIC_API_URL` = public HTTPS URL of the backend (**no trailing slash**)
5. Deploy. After the backend URL changes, update this var and **redeploy** (it is inlined at build time).

No project-specific `vercel.json` is required.

---

## 4. CORS

CORS is fully environment-driven via `CORS_ORIGINS` (comma-separated).

- Configured in: `backend/app/core/config.py` (`CORS_ORIGINS` → `cors_origins_list`)
- Applied in: `backend/app/main.py` (`CORSMiddleware`)

Set in the backend dashboard to your Vercel origin(s), e.g.:

```text
CORS_ORIGINS=https://your-app.vercel.app
```

No code change needed when the frontend URL changes.

---

## 5. Production env vars

### Backend (Render / Railway)

| Variable | Kind | Notes |
|---|---|---|
| `DATABASE_URL` | **secret** (credentials) | Managed Postgres URL; `postgres://` is normalized to `postgresql+psycopg2://` |
| `DATABASE_URL_ASYNC` | plain / optional | Reserved; set if you use async later |
| `CORS_ORIGINS` | plain | Vercel HTTPS origin(s), comma-separated |
| `ENVIRONMENT` | plain | `production` |
| `DEBUG` | plain | `false` |
| `AI_PROVIDER` | plain | `openrouter` or `openai` |
| `OPENROUTER_API_KEY` | **secret** | Required if `AI_PROVIDER=openrouter` |
| `OPENAI_API_KEY` | **secret** | Required if `AI_PROVIDER=openai` (also used for embeddings with OpenAI) |
| `OPENROUTER_MODEL` | plain | e.g. `openai/gpt-4o-mini` |
| `OPENAI_MODEL` | plain | e.g. `gpt-4o-mini` |
| `OPENROUTER_BASE_URL` | plain | Default `https://openrouter.ai/api/v1` |
| `EMBEDDING_MODEL` | plain | e.g. `text-embedding-3-small` |
| `RAG_TOP_K` | plain | Default `4` |
| `RAG_MIN_SIMILARITY` | plain | Default `0.28` |
| `RATE_LIMIT_PER_MINUTE` | plain | Default `30` |
| `LLM_MAX_RETRIES` | plain | Default `2` |
| `LLM_RETRY_BACKOFF_SECONDS` | plain | Default `0.6` |
| `LLM_TIMEOUT_SECONDS` | plain | Default `45` |
| `CONVERSATION_RETENTION_DAYS` | plain | Default `30` |
| `APP_NAME` / `APP_VERSION` | plain | Optional |
| `PORT` | plain | Set by the host; image defaults to `8000` |

Templates: `backend/.env.example`.

### Frontend (Vercel)

| Variable | Kind | Notes |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | plain | Public backend base URL (HTTPS). Not a secret, but do not point at internal-only hosts. |

Template: `frontend/.env.example`.

---

## 6. Smoke test after deploy

- [ ] `GET https://<api>/health` → OK  
- [ ] `GET https://<api>/docs` lists routes  
- [ ] Frontend loads; chat / recommend / compare work cross-origin (CORS)  
- [ ] Knowledge ask works only if pgvector + ingest completed  
- [ ] Disclaimer visible in UI footer  

---

## Local Docker Compose (optional)

```bash
# Set OPENROUTER_API_KEY in the environment, then:
docker compose up --build db api
```

Frontend separately: `NEXT_PUBLIC_API_URL=http://localhost:8000`.

---

## pgvector note

- Migration creates the extension: `CREATE EXTENSION IF NOT EXISTS vector`
- Windows local install: `backend/docs/PGVECTOR_WINDOWS.md`
- Linux / managed production: enable the extension on the host (SQL above), then migrate
