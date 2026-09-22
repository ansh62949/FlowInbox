#!/bin/sh
set -e

echo "Running database migrations..."
alembic upgrade head || alembic stamp head

echo "Starting Uvicorn application server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000

