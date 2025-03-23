#!/bin/sh
set -e

# Wait for a bit to ensure DB is ready (if using external DB)
# sleep 2

cd /app

# Run migrations
echo "Running database migrations..."
python -m alembic -c backend/alembic.ini upgrade head

# Start the application
echo "Starting application..."
exec "$@" 