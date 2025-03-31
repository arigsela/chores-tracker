#!/bin/sh
set -e

echo "Waiting for MySQL database to be ready..."
DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
DB_PORT=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')

echo "Attempting to connect to MySQL at $DB_HOST:$DB_PORT"

# Wait for database to be ready
until nc -z $DB_HOST $DB_PORT; do
    echo "MySQL is unavailable - sleeping"
    sleep 2
done

echo "MySQL is up - executing migrations"

# Set PYTHONPATH and run migrations
export PYTHONPATH=/app
cd /app
python -m alembic -c /app/backend/alembic.ini upgrade head

# Start the application
echo "Starting application..."
exec "$@"
