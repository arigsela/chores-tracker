"""
Metrics endpoint authentication and access control.

Protects the /metrics endpoint from unauthorized access using IP whitelisting
and optional bearer token authentication.
"""

import logging
from ipaddress import ip_address, ip_network, AddressValueError
from typing import List, Optional

from fastapi import Request, HTTPException, Depends

logger = logging.getLogger(__name__)


class MetricsAccessControl:
    """
    Access control for the /metrics endpoint.

    Supports both IP whitelist (preferred) and bearer token authentication.
    """

    def __init__(self, allowed_ips: List[str], auth_token: Optional[str] = None):
        """
        Initialize metrics access control.

        Args:
            allowed_ips: List of allowed IP addresses/CIDR ranges.
                        Example: ["127.0.0.1", "10.0.0.0/8", "192.168.0.0/16"]
            auth_token: Optional bearer token for authentication
        """
        self.allowed_ips = allowed_ips
        self.auth_token = auth_token

    def is_ip_allowed(self, ip: str) -> bool:
        """
        Check if an IP address is in the allowed list.

        Supports both single IPs and CIDR ranges.

        Args:
            ip: IP address to check

        Returns:
            True if IP is allowed, False otherwise
        """
        try:
            client = ip_address(ip)
        except (ValueError, AddressValueError):
            logger.debug(f"Invalid IP address in request: {ip}")
            return False

        for allowed in self.allowed_ips:
            try:
                if "/" in allowed:
                    # CIDR notation
                    if client in ip_network(allowed, strict=False):
                        return True
                else:
                    # Single IP
                    if str(client) == allowed:
                        return True
            except (ValueError, AddressValueError):
                logger.debug(f"Invalid IP pattern: {allowed}")
                continue

        return False

    def is_token_valid(self, token: Optional[str]) -> bool:
        """
        Check if bearer token is valid.

        Args:
            token: Bearer token from Authorization header

        Returns:
            True if token is valid, False otherwise
        """
        if not self.auth_token:
            return False  # Token auth disabled if not configured

        return token == self.auth_token

    async def check_access(self, request: Request) -> None:
        """
        Check if request is allowed to access /metrics.

        First tries IP whitelist, then falls back to bearer token.

        Args:
            request: FastAPI Request object

        Raises:
            HTTPException: If access is denied (403 Forbidden)
        """
        client_ip = request.client.host if request.client else "unknown"

        # Try IP whitelist first (preferred method)
        if self.is_ip_allowed(client_ip):
            logger.debug(f"Metrics access allowed for IP: {client_ip}")
            return

        # Fall back to bearer token if IP check fails
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove "Bearer " prefix
            if self.is_token_valid(token):
                logger.info(f"Metrics access allowed via token for IP: {client_ip}")
                return

        # Access denied
        logger.warning(f"Metrics access denied for IP: {client_ip}")
        raise HTTPException(
            status_code=403,
            detail="Access to metrics endpoint is forbidden"
        )


# Global instance (initialized in main.py during app startup)
metrics_access_control: Optional[MetricsAccessControl] = None


async def check_metrics_access(request: Request) -> None:
    """
    FastAPI dependency to check metrics endpoint access.

    This dependency should be added to the /metrics endpoint to enforce access control.

    Usage:
        @app.get("/metrics", dependencies=[Depends(check_metrics_access)])
        async def metrics_endpoint():
            return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    Args:
        request: FastAPI Request object

    Raises:
        HTTPException: If access is denied
    """
    if metrics_access_control is None:
        raise HTTPException(
            status_code=500,
            detail="Metrics access control not initialized"
        )

    await metrics_access_control.check_access(request)
