"""API8:2023 - Security Misconfiguration

Tests that errors don't leak stack traces, security headers are present,
and debug endpoints are properly controlled.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestErrorHandling:
    async def test_404_no_stack_trace(self, client: AsyncClient, auth_headers: dict):
        """404 errors should not contain stack traces or internal details."""
        response = await client.get("/api/v1/nonexistent", headers=auth_headers)
        assert response.status_code in (404, 405)
        body = response.text
        assert "Traceback" not in body
        assert "File" not in body
        assert "sqlalchemy" not in body.lower()

    async def test_validation_error_safe(self, client: AsyncClient, auth_headers: dict):
        """Validation errors should show field details but no internals."""
        response = await client.post("/api/v1/horses/", json={
            "name": "x" * 200,
        }, headers=auth_headers)
        assert response.status_code == 422
        body = response.text
        assert "Traceback" not in body


@pytest.mark.asyncio
class TestSecurityHeaders:
    async def test_x_content_type_options(self, client: AsyncClient, auth_headers: dict):
        """X-Content-Type-Options: nosniff must be present."""
        response = await client.get("/api/v1/users/me", headers=auth_headers)
        assert response.headers.get("X-Content-Type-Options") == "nosniff"

    async def test_x_frame_options(self, client: AsyncClient, auth_headers: dict):
        """X-Frame-Options: DENY must be present."""
        response = await client.get("/api/v1/users/me", headers=auth_headers)
        assert response.headers.get("X-Frame-Options") == "DENY"

    async def test_strict_transport_security(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Strict-Transport-Security must be present."""
        response = await client.get("/api/v1/users/me", headers=auth_headers)
        hsts = response.headers.get("Strict-Transport-Security")
        assert hsts is not None
        assert "max-age" in hsts

    async def test_cache_control_no_store(self, client: AsyncClient, auth_headers: dict):
        """Cache-Control: no-store must be present on API responses."""
        response = await client.get("/api/v1/users/me", headers=auth_headers)
        assert response.headers.get("Cache-Control") == "no-store"

    async def test_csp_header(self, client: AsyncClient, auth_headers: dict):
        """Content-Security-Policy must be present."""
        response = await client.get("/api/v1/users/me", headers=auth_headers)
        assert response.headers.get("Content-Security-Policy") is not None

    async def test_request_id_present(self, client: AsyncClient, auth_headers: dict):
        """X-Request-ID must be present for tracing."""
        response = await client.get("/api/v1/users/me", headers=auth_headers)
        assert response.headers.get("X-Request-ID") is not None


@pytest.mark.asyncio
class TestPasswordResetInfoLeak:
    async def test_password_reset_generic_response(self, client: AsyncClient):
        """Password reset should return the same message whether email exists or not."""
        resp_exists = await client.post("/api/v1/auth/password-reset/request", json={
            "email": "exists@example.com",
        })
        resp_not_exists = await client.post("/api/v1/auth/password-reset/request", json={
            "email": "doesnotexist@example.com",
        })
        assert resp_exists.status_code == resp_not_exists.status_code
        assert resp_exists.json()["detail"] == resp_not_exists.json()["detail"]
