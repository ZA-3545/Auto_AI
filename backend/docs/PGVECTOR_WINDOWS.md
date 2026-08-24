# Install pgvector (Windows / PostgreSQL 18) for AutoAI RAG
#
# 1. Download the matching zip from:
#    https://github.com/andreiramani/pgvector_pgsql_windows/releases
#    (e.g. vector.v0.8.6-pg18.zip)
# 2. Run PowerShell as Administrator and copy into your Postgres install:
#      Copy-Item .\lib\vector.dll "C:\Program Files\PostgreSQL\18\lib\" -Force
#      Copy-Item .\share\extension\* "C:\Program Files\PostgreSQL\18\share\extension\" -Force
# 3. Restart PostgreSQL, then:
#      CREATE EXTENSION IF NOT EXISTS vector;
# 4. From backend/: alembic upgrade head
# 5. Ingest sample knowledge:
#      python -m app.scripts.ingest_knowledge
