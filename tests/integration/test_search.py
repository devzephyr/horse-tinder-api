import pytest
from httpx import AsyncClient

from app.models.horse import Horse


@pytest.mark.asyncio
class TestSearch:
    async def test_search_by_breed(
        self, client: AsyncClient, auth_headers: dict, test_horse: Horse
    ):
        response = await client.get(
            "/api/v1/search/horses?breed=Arabian", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert all("Arabian" in h["breed"] for h in data["items"])

    async def test_search_by_temperament(
        self, client: AsyncClient, auth_headers: dict, test_horse: Horse
    ):
        response = await client.get(
            "/api/v1/search/horses?temperament=spirited", headers=auth_headers
        )
        assert response.status_code == 200

    async def test_search_by_age_range(
        self, client: AsyncClient, auth_headers: dict, test_horse: Horse
    ):
        response = await client.get(
            "/api/v1/search/horses?min_age=3&max_age=10", headers=auth_headers
        )
        assert response.status_code == 200

    async def test_search_pagination(
        self, client: AsyncClient, auth_headers: dict
    ):
        response = await client.get(
            "/api/v1/search/horses?page=1&page_size=5", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 5

    async def test_search_no_results(
        self, client: AsyncClient, auth_headers: dict
    ):
        response = await client.get(
            "/api/v1/search/horses?breed=NonExistentBreed", headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["total"] == 0

    async def test_search_requires_auth(self, client: AsyncClient):
        response = await client.get("/api/v1/search/horses")
        assert response.status_code == 401
