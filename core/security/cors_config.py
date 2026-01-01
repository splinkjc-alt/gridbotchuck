"""
CORS (Cross-Origin Resource Sharing) configuration.
Provides secure CORS settings for the API server.
"""

import os

from aiohttp_cors import ResourceOptions, setup


def setup_cors_secure(app):
    """
    Setup CORS with secure defaults.
    
    By default, only allows localhost for development.
    Configure ALLOWED_ORIGINS environment variable for production.
    
    Args:
        app: aiohttp Application instance
        
    Returns:
        CORS instance
    """
    # Get allowed origins from environment
    allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "http://localhost:8080,http://127.0.0.1:8080")
    allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",")]
    
    # Create CORS configuration
    cors_config = {}
    
    for origin in allowed_origins:
        cors_config[origin] = ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        )
    
    # Setup CORS
    cors = setup(app, defaults=cors_config)
    
    # Apply CORS to all routes
    for route in list(app.router.routes()):
        try:
            cors.add(route)
        except ValueError:
            # Route already has CORS or is not applicable
            pass
    
    return cors
