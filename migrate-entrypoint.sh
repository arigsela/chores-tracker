#!/bin/sh
set -e

echo "=== Database Migration Job ==="
echo "Starting at: $(date)"

# Extract database connection details from DATABASE_URL
DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
DB_PORT=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')

echo "Database host: $DB_HOST"
echo "Database port: $DB_PORT"

# Wait for database to be ready
echo "Waiting for MySQL database to be ready..."
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

echo "MySQL is up - checking current migration state..."

# Set PYTHONPATH and navigate to app directory
export PYTHONPATH=/app
cd /app

# Show current migration version
echo "Current database migration version:"
python -m alembic -c /app/backend/alembic.ini current || {
    echo "WARNING: Could not determine current migration version (this might be a fresh database)"
}

# Show available migrations
echo ""
echo "Available migrations:"
python -m alembic -c /app/backend/alembic.ini heads

# Run migrations with verbose output
echo ""
echo "Running migrations..."
python -m alembic -c /app/backend/alembic.ini upgrade head

# Verify final state
echo ""
echo "Migration complete! Final database version:"
python -m alembic -c /app/backend/alembic.ini current

echo "Migration job completed successfully at: $(date)"
exit 0
