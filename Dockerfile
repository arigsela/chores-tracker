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

# Register OpenTelemetry auto-instrumentations detected from installed packages.
# Safe to run even if individual instrumentation packages are already pinned in
# requirements.txt — this just wires them into the entry-point config.
RUN opentelemetry-bootstrap -a install

# Copy source code
COPY backend /app/backend

# Copy entrypoint scripts
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
COPY migrate-entrypoint.sh /app/migrate-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh /app/migrate-entrypoint.sh

# Verify files are present (debugging)
RUN ls -la /app/backend && \
    ls -la /app/backend/alembic.ini

EXPOSE 8000

# Set entrypoint
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Run the application under the OpenTelemetry auto-instrumentation wrapper.
# The SDK is a no-op unless OTEL_EXPORTER_OTLP_ENDPOINT (and OTEL_TRACES_EXPORTER)
# env vars are set at runtime — configured via the Kubernetes ConfigMap.
CMD ["opentelemetry-instrument", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
