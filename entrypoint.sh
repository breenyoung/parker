#!/bin/sh
# entrypoint.sh

# Stop on errors
set -e

# Create the storage structure inside the mounted volume
# Because this runs at runtime, it writes to your local ./data folder!
mkdir -p /app/storage/database \
         /app/storage/cache \
         /app/storage/cover \
         /app/storage/avatars \
         /app/storage/logs

# Run the database migrations
echo "Running migrations..."
alembic upgrade head

# Start the application
echo "Starting Parker..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000