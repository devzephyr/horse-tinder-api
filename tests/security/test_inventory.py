"""API9:2023 - Improper Inventory Management

Tests that there are no shadow APIs, deprecated endpoints,
or unversioned access paths.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestInventoryManagement:
    async def test_no_v2_api(self, client: AsyncClient, auth_headers: dict):
        """There should be no /api/v2/ endpoints (shadow API)."""
        response = await client.get("/api/v2/horses", headers=auth_headers)
        assert response.status_code in (404, 405)

    async def test_no_unversioned_api(self, client: AsyncClient, auth_headers: dict):
        """There should be no /api/horses (unversioned) endpoint."""
        response = await client.get("/api/horses", headers=auth_headers)
        assert response.status_code in (404, 405)

    async def test_no_root_api(self, client: AsyncClient, auth_headers: dict):
        """There should be no /horses endpoint at root level."""
        response = await client.get("/horses", headers=auth_headers)
        assert response.status_code in (404, 405)

    async def test_all_endpoints_under_v1(self, client: AsyncClient):
        """Verify critical endpoints are only accessible under /api/v1/."""
        from app.main import app

        for route in app.routes:
            if hasattr(route, "path") and route.path.startswith("/api/"):
                assert route.path.startswith("/api/v1/"), (
                    f"Route {route.path} is not under /api/v1/"
                )

    async def test_openapi_schema_available_in_dev(self, client: AsyncClient):
        """OpenAPI schema should be available in development mode."""
        response = await client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert schema["info"]["title"] == "Horse Tinder API"
        assert "paths" in schema
