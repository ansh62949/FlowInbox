#!/bin/sh

echo "Running database migrations with Alembic..."
alembic upgrade head || echo "Warning: Alembic migration skipped or failed"

echo "Starting Uvicorn application server..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"

