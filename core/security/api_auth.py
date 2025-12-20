"""
API Authentication middleware for GridBot Pro.

Provides token-based authentication to protect REST API endpoints
from unauthorized access.
"""

import hashlib
import hmac
import logging
import os
from pathlib import Path
import secrets

from aiohttp import web

logger = logging.getLogger(__name__)


def generate_api_token(length: int = 32) -> str:
    """Generate a secure random API token."""
    return secrets.token_urlsafe(length)


def _get_or_create_api_token() -> str:
    """Get API token from environment or create one if not exists."""
    # First check environment variable
    token = os.environ.get("GRIDBOT_API_TOKEN")
    if token:
        return token

    # Check for token file
    token_file = Path.home() / ".gridbot" / "api_token"
    if token_file.exists():
        return token_file.read_text().strip()

    # Generate and save new token
    token = generate_api_token()
    token_file.parent.mkdir(parents=True, exist_ok=True)
    token_file.write_text(token)
    token_file.chmod(0o600)  # Read/write only for owner

    logger.info(f"Generated new API token. Saved to {token_file}")
    logger.info("Set GRIDBOT_API_TOKEN environment variable to use a custom token.")

    return token


class APIAuthMiddleware:
    """
    Middleware for API token authentication.

    Validates requests using Bearer token authentication.
    Public endpoints (health check, static files) bypass authentication.
    """

    # Endpoints that don't require authentication
    PUBLIC_ENDPOINTS = frozenset(
        {
            "/",
            "/api/health",
            "/styles.css",
            "/script.js",
        }
    )

    # Endpoint prefixes that don't require authentication
    PUBLIC_PREFIXES = ("/static/",)

    def __init__(self, api_token: str | None = None):
        """
        Initialize the authentication middleware.

        Args:
            api_token: API token for authentication. If not provided,
                      will use GRIDBOT_API_TOKEN env var or generate one.
        """
        self._api_token = api_token or _get_or_create_api_token()
        self._token_hash = hashlib.sha256(self._api_token.encode()).hexdigest()

    @property
    def api_token(self) -> str:
        """Get the API token (for displaying to user on first run)."""
        return self._api_token

    def _is_public_endpoint(self, path: str) -> bool:
        """Check if the endpoint is public (no auth required)."""
        if path in self.PUBLIC_ENDPOINTS:
            return True

        return any(path.startswith(prefix) for prefix in self.PUBLIC_PREFIXES)

    def _validate_token(self, request: web.Request) -> bool:
        """Validate the authentication token from the request."""
        # Check Authorization header
        auth_header = request.headers.get("Authorization", "")

        if auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove "Bearer " prefix
            # Use constant-time comparison to prevent timing attacks
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            return hmac.compare_digest(token_hash, self._token_hash)

        # Check X-API-Key header (alternative auth method)
        api_key = request.headers.get("X-API-Key", "")
        if api_key:
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            return hmac.compare_digest(key_hash, self._token_hash)

        # Check query parameter (for WebSocket connections)
        token = request.query.get("token", "")
        if token:
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            return hmac.compare_digest(token_hash, self._token_hash)

        return False

    @web.middleware
    async def middleware(self, request: web.Request, handler):
        """
        Authentication middleware handler.

        Validates API token for protected endpoints.
        """
        path = request.path

        # Allow public endpoints without authentication
        if self._is_public_endpoint(path):
            return await handler(request)

        # Validate authentication for protected endpoints
        if not self._validate_token(request):
            logger.warning(
                f"Unauthorized access attempt to {path} "
                f"from {request.remote}"
            )
            raise web.HTTPUnauthorized(
                text="Invalid or missing API token. "
                "Use 'Authorization: Bearer <token>' header."
            )

        return await handler(request)


def _mask_token(token: str) -> str:
    """Mask a token for safe display (shows first/last 4 characters)."""
    if len(token) <= 12:
        return "*" * len(token)
    return f"{token[:4]}...{token[-4:]}"


def get_api_token_info(mask_token: bool = False) -> dict:
    """
    Get information about the current API token configuration.

    Args:
        mask_token: If True, mask the token for safe display.

    Returns:
        dict with token info and instructions.
    """
    token = _get_or_create_api_token()
    token_file = Path.home() / ".gridbot" / "api_token"

    display_token = _mask_token(token) if mask_token else token

    return {
        "token": token,
        "token_masked": _mask_token(token),
        "token_file": str(token_file),
        "env_var": "GRIDBOT_API_TOKEN",
        "usage": {
            "header": f"Authorization: Bearer {display_token}",
            "curl_example": f'curl -H "Authorization: Bearer {display_token}" http://localhost:8080/api/bot/status',
        },
    }
