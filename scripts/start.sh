#!/bin/bash
set -e

# Run database migrations
echo "Running database migrations..."
cd backend && alembic upgrade head

# Start the application with Docker Compose
echo "Starting application..."
docker-compose up --build