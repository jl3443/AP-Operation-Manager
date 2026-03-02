#!/bin/bash
set -e

echo "==> Running Alembic migrations..."
cd /app
alembic upgrade head || {
  echo "  Migration failed (tables likely exist already), skipping..."
}

echo "==> Seeding database (idempotent)..."
python -m app.seed

echo "==> Ensuring MinIO bucket exists..."
python -c "
from app.services.s3_service import ensure_bucket_exists, get_s3_client
ensure_bucket_exists(get_s3_client())
print('  Bucket ready')
"

echo "==> Starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
