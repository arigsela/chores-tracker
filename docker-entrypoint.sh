#!/bin/sh
set -e

# Wait for database if needed (for MySQL)
if [ "$DATABASE_URL" != "${DATABASE_URL#mysql}" ]; then
    echo "Waiting for MySQL database to be ready..."
    # Extract host and port from DATABASE_URL
    DB_HOST=$(echo $DATABASE_URL | sed -E 's/.*@([^:]+):.*/\1/')
    DB_PORT=$(echo $DATABASE_URL | sed -E 's/.*:([0-9]+)\/.*/\1/')
    
    # If we couldn't extract, use defaults
    DB_HOST=${DB_HOST:-localhost}
    DB_PORT=${DB_PORT:-3306}
    
    # Wait for database to be ready
    MAX_RETRIES=30
    RETRY_COUNT=0
    until nc -z $DB_HOST $DB_PORT || [ $RETRY_COUNT -eq $MAX_RETRIES ]; do
        >&2 echo "MySQL is unavailable - sleeping"
        RETRY_COUNT=$((RETRY_COUNT+1))
        sleep 2
    done
    
    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        >&2 echo "MySQL is not available after $MAX_RETRIES retries. Exiting."
        exit 1
    fi
    
    >&2 echo "MySQL is up - executing command"
fi

cd /app

# Run migrations
echo "Running database migrations..."
python -m alembic -c backend/alembic.ini upgrade head

# Start the application
echo "Starting application..."
exec "$@" 