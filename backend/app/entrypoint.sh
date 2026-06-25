#!/bin/bash
set -e

# Run database migrations to create tables
echo "Running Alembic migrations..."
alembic upgrade head

# Start FastAPI application
echo "Starting FastAPI server..."
exec uvicorn app.main:app "$@"