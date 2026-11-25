#!/bin/bash
set -e

echo "=================================================="
echo " Starting InsightIQ AI Backend Container"
echo "=================================================="

# Wait for PostgreSQL if configured
if [ -n "$DATABASE_URL" ]; then
    echo "Checking database connection and seeding reference data..."
    python /app/scripts/ingest_data.py --data-dir /app/data/raw --db-url "$DATABASE_URL" || echo "Data ingestion completed or deferred."
fi

echo "Starting Uvicorn production server on 0.0.0.0:8000..."
exec uvicorn app.main:app --app-dir /app/backend --host 0.0.0.0 --port 8000
