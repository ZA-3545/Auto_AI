# Privacy & data retention (PLANNING.md Section J)

**Independent proof of concept — not affiliated with or endorsed by PakWheels.**

## What we store

- Anonymous `conversations` and `messages` for session memory (budget, city, transmission preferences, etc.).
- No user accounts or personal identity in this PoC (authentication is future work).
- Demo vehicle catalog and educational knowledge chunks (not personal data).

## Retention policy

| Data | Retention | Action |
|---|---|---|
| Conversations / messages | **30 days** after last update (`CONVERSATION_RETENTION_DAYS`) | Delete conversation + related messages |
| Immediate clear | On demand | **Start new search** / `POST /api/chat/reset` |
| Vehicle & knowledge demo data | Until reseeding | Not personal data |

### Operator command

```bash
cd backend
python -m app.scripts.purge_old_conversations --days 30
python -m app.scripts.purge_old_conversations --days 30 --dry-run
```

Schedule this (cron / Render cron / GitHub Action) in production. Default window matches `CONVERSATION_RETENTION_DAYS` in `backend/.env`.

## Guidance for users of this PoC

- Treat chat content as non-sensitive demo input.
- Do not paste real CNICs, bank details, or private documents.
- Listing analyzer and knowledge answers are informational only — not professional mechanical or financial advice.
