"""
API Authentication and Authorization middleware.
Provides API key-based authentication for the REST API server.
"""

import hashlib
import logging
import os
import secrets
from functools import wraps

from aiohttp import web


class APIAuth:
    """
    API authentication handler using API keys.
    Supports both environment variable and generated API keys.
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.api_key = self._get_or_generate_api_key()
        
    def _get_or_generate_api_key(self) -> str:
        """
        Get API key from environment or generate a secure one.
        
        Returns:
            API key string
        """
        # Try to get from environment first
        api_key = os.getenv("GRIDBOT_API_KEY")
        
        if api_key:
            self.logger.info("Using API key from environment variable GRIDBOT_API_KEY")
            return api_key
        
        # Generate a secure random API key
        api_key = secrets.token_urlsafe(32)
        self.logger.warning(
            f"No GRIDBOT_API_KEY found in environment. Generated temporary API key: {api_key}"
        )
        self.logger.warning(
            "Add GRIDBOT_API_KEY to your .env file to use a persistent key."
        )
        return api_key
    
    def verify_api_key(self, provided_key: str) -> bool:
        """
        Verify the provided API key matches the configured key.
        Uses constant-time comparison to prevent timing attacks.
        
        Args:
            provided_key: API key to verify
            
        Returns:
            True if valid, False otherwise
        """
        if not provided_key:
            return False
        
        return secrets.compare_digest(
            hashlib.sha256(provided_key.encode()).digest(),
            hashlib.sha256(self.api_key.encode()).digest()
        )
    
    @staticmethod
    def auth_required(handler):
        """
        Decorator to require API key authentication for endpoints.
        
        Usage:
            @auth_required
            async def handle_endpoint(self, request):
                ...
        """
        @wraps(handler)
        async def wrapped(self, request):
            # Get API key from Authorization header or query parameter
            auth_header = request.headers.get("Authorization", "")
            api_key = None
            
            if auth_header.startswith("Bearer "):
                api_key = auth_header[7:]
            elif "api_key" in request.query:
                api_key = request.query["api_key"]
            
            # Verify API key
            if not hasattr(self, "api_auth") or not self.api_auth.verify_api_key(api_key):
                return web.json_response(
                    {
                        "success": False,
                        "error": "Unauthorized",
                        "message": "Invalid or missing API key. Include 'Authorization: Bearer <key>' header or '?api_key=<key>' parameter."
                    },
                    status=401
                )
            
            return await handler(self, request)
        
        return wrapped


def create_api_auth_middleware(api_auth: APIAuth):
    """
    Create middleware for API authentication.
    
    Args:
        api_auth: APIAuth instance
        
    Returns:
        Middleware function
    """
    @web.middleware
    async def auth_middleware(request, handler):
        # Skip authentication for health check and static files
        if (request.path == "/api/health" or 
            request.path.startswith("/static") or
            request.path.endswith((".html", ".css", ".js", ".png", ".jpg", ".svg")) or
            request.path == "/"):
            return await handler(request)
        
        # Check if this is an API endpoint
        if request.path.startswith("/api/"):
            # Get API key from Authorization header or query parameter
            auth_header = request.headers.get("Authorization", "")
            api_key = None
            
            if auth_header.startswith("Bearer "):
                api_key = auth_header[7:]
            elif "api_key" in request.query:
                api_key = request.query["api_key"]
            
            # Verify API key
            if not api_auth.verify_api_key(api_key):
                return web.json_response(
                    {
                        "success": False,
                        "error": "Unauthorized",
                        "message": "Invalid or missing API key. Include 'Authorization: Bearer <key>' header or '?api_key=<key>' parameter."
                    },
                    status=401
                )
        
        return await handler(request)
    
    return auth_middleware
