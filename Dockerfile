FROM python:3.11-slim

WORKDIR /app

# Set environment variables
ENV PYTHONPATH="/app" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    ENVIRONMENT="production"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    pkg-config \
    build-essential \
    netcat-traditional \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY backend/requirements.txt .
RUN pip install -U pip && pip install -r requirements.txt

# Copy source code
COPY backend /app/backend

# Copy entrypoint script
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

# Verify files are present (debugging)
RUN ls -la /app/backend && \
    ls -la /app/backend/alembic.ini

EXPOSE 8000

# Set entrypoint
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Run the application
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
