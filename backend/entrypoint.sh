#!/usr/bin/env bash
set -e

echo "Creating upload directories..."
mkdir -p /app/uploads/documents
chmod 755 /app/uploads/documents
echo "Upload directories created successfully"

echo "Waiting for database to be ready..."
python -m app.prestart

echo "Running database migrations..."
alembic upgrade head

echo "Starting FastAPI with Uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000

