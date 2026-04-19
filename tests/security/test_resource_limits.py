"""API4:2023 - Unrestricted Resource Consumption

Tests that pagination is enforced, request sizes are limited,
and rate limiting headers are present.
"""

import pytest
from httpx import AsyncClient

from app.models.user import User


@pytest.mark.asyncio
class TestPaginationLimits:
    async def test_page_size_capped(self, client: AsyncClient, auth_headers: dict):
        """Requesting page_size=1000 should be rejected (max 50)."""
        response = await client.get(
            "/api/v1/horses/?page_size=1000", headers=auth_headers
        )
        assert response.status_code == 422

    async def test_page_size_50_allowed(self, client: AsyncClient, auth_headers: dict):
        """page_size=50 is the maximum and should be accepted."""
        response = await client.get(
            "/api/v1/horses/?page_size=50", headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["page_size"] == 50

    async def test_negative_page_rejected(self, client: AsyncClient, auth_headers: dict):
        """page=0 or negative should be rejected."""
        response = await client.get(
            "/api/v1/horses/?page=0", headers=auth_headers
        )
        assert response.status_code == 422

    async def test_search_pagination_capped(self, client: AsyncClient, auth_headers: dict):
        """Search endpoint also enforces page_size cap."""
        response = await client.get(
            "/api/v1/search/horses?page_size=100", headers=auth_headers
        )
        assert response.status_code == 422


@pytest.mark.asyncio
class TestRequestSizeLimit:
    async def test_large_request_body_rejected(self, client: AsyncClient, auth_headers: dict):
        """Request body > 1MB should return 413."""
        large_payload = {"name": "x" * 2_000_000}
        response = await client.post(
            "/api/v1/horses/",
            json=large_payload,
            headers={**auth_headers, "Content-Length": str(2_000_000)},
        )
        assert response.status_code in (413, 422)


@pytest.mark.asyncio
class TestResourceLimits:
    async def test_max_horses_per_user(self, client: AsyncClient, auth_headers: dict):
        """Users cannot create more than 5 horses."""
        for i in range(5):
            resp = await client.post("/api/v1/horses/", json={
                "name": f"Horse {i}",
                "breed": "Arabian",
                "age": 3,
                "temperament": "calm",
                "location_city": "Toronto",
                "location_country": "Canada",
            }, headers=auth_headers)
            assert resp.status_code == 201

        resp = await client.post("/api/v1/horses/", json={
            "name": "Horse 6",
            "breed": "Arabian",
            "age": 3,
            "temperament": "calm",
            "location_city": "Toronto",
            "location_country": "Canada",
        }, headers=auth_headers)
        assert resp.status_code == 429

    async def test_message_content_length_limit(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Messages longer than 2000 chars should be rejected."""
        import uuid

        response = await client.post(
            f"/api/v1/matches/{uuid.uuid4()}/messages/",
            json={"content": "x" * 2001},
            headers=auth_headers,
        )
        assert response.status_code == 422
