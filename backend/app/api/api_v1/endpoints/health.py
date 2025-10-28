"""
Health check endpoints for monitoring and infrastructure.

These endpoints follow Kubernetes health check patterns:
- /health: Basic liveness probe
- /health/ready: Readiness probe with dependency checks
- /health/detailed: Component-level diagnostics
"""
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from ....db.base import get_db
from datetime import datetime

router = APIRouter()


@router.get("/health")
async def basic_health():
    """
    Basic liveness check - no dependencies.

    Returns 200 if the application process is running.
    Used by: Kubernetes liveness probes, load balancers.
    """
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/health/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """
    Readiness check - verifies database connectivity.

    Returns 200 only if the application can serve traffic.
    Used by: Kubernetes readiness probes, load balancers.
    """
    try:
        # Simple query to verify database connection
        await db.execute(text("SELECT 1"))
        return {
            "status": "ready",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "database": "disconnected",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get("/health/detailed")
async def detailed_health(db: AsyncSession = Depends(get_db)):
    """
    Detailed health check - returns component-level status.

    Used by: Monitoring tools, debugging, dashboards.
    Returns 200 if all components healthy, 503 if any component unhealthy.
    """
    components = {}
    overall_healthy = True

    # Check database connectivity and version
    try:
        result = await db.execute(text("SELECT VERSION()"))
        db_version = result.scalar()
        components["database"] = {
            "status": "healthy",
            "version": db_version,
            "type": "MySQL"
        }
    except Exception as e:
        components["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        overall_healthy = False

    # Future: Add more component checks here
    # - Cache connectivity (Redis, if added)
    # - External API availability
    # - File storage access
    # - Message queue status

    response_code = status.HTTP_200_OK if overall_healthy else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=response_code,
        content={
            "status": "healthy" if overall_healthy else "unhealthy",
            "components": components,
            "timestamp": datetime.utcnow().isoformat(),
            "version": "3.0.0"
        }
    )
