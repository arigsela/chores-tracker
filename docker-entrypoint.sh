#!/bin/sh
set -e

echo "Waiting for MySQL database to be ready..."
DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
DB_PORT=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')

echo "Attempting to connect to MySQL at $DB_HOST:$DB_PORT"

# Wait for database to be ready
MAX_RETRIES=30
RETRY_COUNT=0

until nc -z $DB_HOST $DB_PORT; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "ERROR: MySQL not available after $MAX_RETRIES attempts"
        exit 1
    fi
    echo "MySQL is unavailable (attempt $RETRY_COUNT/$MAX_RETRIES) - sleeping 2 seconds"
    sleep 2
done

echo "MySQL is up - database migrations should be handled by migration job"

# Increase file descriptor limits to prevent "too many open files" errors
# This is particularly important for production workloads with high concurrency
ulimit -n 65536 2>/dev/null || echo "Warning: Could not set ulimit (may need pod securityContext)"

echo "Starting application..."
exec "$@"
