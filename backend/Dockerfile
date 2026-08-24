# AutoAI API — production container (Phase 8 / PLANNING.md C.1)
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY alembic.ini .
COPY alembic ./alembic
COPY app ./app

# Do not copy .env — inject secrets at runtime via the host platform
EXPOSE 8000

# Migrations / seed / knowledge ingest are one-off jobs (see docs/DEPLOYMENT.md).
# Shell form so $PORT expands (Render, Railway, and similar set PORT).
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}
