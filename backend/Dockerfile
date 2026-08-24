# AutoAI API — production-ready container (Phase 8)
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY alembic.ini .
COPY alembic ./alembic
COPY app ./app

# Do not copy .env — inject secrets at runtime
EXPOSE 8000

# Migrations should be run as a release command / one-off job before serving
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
