"""
Tests for API authentication middleware.
"""

from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase

from core.security.api_auth import APIAuthMiddleware, generate_api_token


class TestGenerateApiToken:
    """Tests for the generate_api_token function."""

    def test_generates_token(self):
        """Test that a token is generated."""
        token = generate_api_token()
        assert token is not None
        assert len(token) > 0

    def test_token_length(self):
        """Test that token has expected length (base64 encoded)."""
        token = generate_api_token(32)
        # URL-safe base64 encoding of 32 bytes = ~43 chars
        assert len(token) >= 32

    def test_generates_unique_tokens(self):
        """Test that generated tokens are unique."""
        tokens = {generate_api_token() for _ in range(100)}
        assert len(tokens) == 100


class TestAPIAuthMiddleware:
    """Tests for the APIAuthMiddleware class."""

    def test_init_with_token(self):
        """Test initialization with a provided token."""
        token = "test-token-12345"  # noqa: S105
        middleware = APIAuthMiddleware(api_token=token)
        assert middleware.api_token == token

    def test_public_endpoint_detection(self):
        """Test that public endpoints are correctly identified."""
        middleware = APIAuthMiddleware(api_token="test")  # noqa: S106

        # Public endpoints
        assert middleware._is_public_endpoint("/") is True
        assert middleware._is_public_endpoint("/api/health") is True
        assert middleware._is_public_endpoint("/styles.css") is True
        assert middleware._is_public_endpoint("/script.js") is True
        assert middleware._is_public_endpoint("/static/file.js") is True

        # Protected endpoints
        assert middleware._is_public_endpoint("/api/bot/status") is False
        assert middleware._is_public_endpoint("/api/bot/start") is False
        assert middleware._is_public_endpoint("/api/config") is False


class TestAPIAuthMiddlewareIntegration(AioHTTPTestCase):
    """Integration tests for the API authentication middleware."""

    async def get_application(self):
        """Create a test application with the auth middleware."""
        self.test_token = "test-secure-token-12345"  # noqa: S105
        self.auth_middleware = APIAuthMiddleware(api_token=self.test_token)

        app = web.Application(middlewares=[self.auth_middleware.middleware])

        # Add test routes
        app.router.add_get("/api/health", self.handle_health)
        app.router.add_get("/api/protected", self.handle_protected)
        app.router.add_get("/", self.handle_root)

        return app

    async def handle_health(self, request):
        """Health endpoint handler (public)."""
        return web.json_response({"status": "ok"})

    async def handle_protected(self, request):
        """Protected endpoint handler."""
        return web.json_response({"data": "secret"})

    async def handle_root(self, request):
        """Root endpoint handler (public)."""
        return web.Response(text="Dashboard")

    async def test_public_endpoint_no_auth(self):
        """Test that public endpoints work without authentication."""
        resp = await self.client.request("GET", "/api/health")
        assert resp.status == 200
        data = await resp.json()
        assert data["status"] == "ok"

    async def test_root_no_auth(self):
        """Test that root endpoint works without authentication."""
        resp = await self.client.request("GET", "/")
        assert resp.status == 200

    async def test_protected_endpoint_no_auth(self):
        """Test that protected endpoints reject requests without auth."""
        resp = await self.client.request("GET", "/api/protected")
        assert resp.status == 401

    async def test_protected_endpoint_wrong_token(self):
        """Test that protected endpoints reject wrong tokens."""
        headers = {"Authorization": "Bearer wrong-token"}
        resp = await self.client.request("GET", "/api/protected", headers=headers)
        assert resp.status == 401

    async def test_protected_endpoint_valid_bearer_token(self):
        """Test that protected endpoints accept valid Bearer token."""
        headers = {"Authorization": f"Bearer {self.test_token}"}
        resp = await self.client.request("GET", "/api/protected", headers=headers)
        assert resp.status == 200
        data = await resp.json()
        assert data["data"] == "secret"

    async def test_protected_endpoint_valid_api_key(self):
        """Test that protected endpoints accept valid X-API-Key header."""
        headers = {"X-API-Key": self.test_token}
        resp = await self.client.request("GET", "/api/protected", headers=headers)
        assert resp.status == 200

    async def test_protected_endpoint_valid_query_token(self):
        """Test that protected endpoints accept valid query parameter token."""
        resp = await self.client.request(
            "GET", f"/api/protected?token={self.test_token}"
        )
        assert resp.status == 200
