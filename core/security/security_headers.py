"""
Security headers middleware for web server.
Adds security headers to protect against common web vulnerabilities.
"""

from aiohttp import web


@web.middleware
async def security_headers_middleware(request, handler):
    """
    Add security headers to all responses.
    
    Headers added:
    - Content-Security-Policy: Prevents XSS attacks
    - X-Frame-Options: Prevents clickjacking
    - X-Content-Type-Options: Prevents MIME sniffing
    - Referrer-Policy: Controls referrer information
    - Permissions-Policy: Controls browser features
    """
    response = await handler(request)
    
    # Content Security Policy - strict policy to prevent XSS
    # Allow self for scripts, styles, and images
    # Allow Chart.js CDN for dashboard charts
    # Allow Google Fonts for typography
    csp_directives = [
        "default-src 'self'",
        "script-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'",  # unsafe-inline needed for Chart.js
        "style-src 'self' https://fonts.googleapis.com 'unsafe-inline'",  # unsafe-inline for inline styles
        "font-src 'self' https://fonts.gstatic.com",
        "img-src 'self' data: https:",
        "connect-src 'self'",
        "frame-ancestors 'none'",
        "base-uri 'self'",
        "form-action 'self'"
    ]
    response.headers["Content-Security-Policy"] = "; ".join(csp_directives)
    
    # Prevent clickjacking
    response.headers["X-Frame-Options"] = "DENY"
    
    # Prevent MIME sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"
    
    # Control referrer information
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # Disable potentially dangerous browser features
    permissions_policy = [
        "accelerometer=()",
        "camera=()",
        "geolocation=()",
        "microphone=()",
        "payment=()"
    ]
    response.headers["Permissions-Policy"] = ", ".join(permissions_policy)
    
    # Strict Transport Security (if using HTTPS)
    # Uncomment when deploying with HTTPS
    # response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return response
