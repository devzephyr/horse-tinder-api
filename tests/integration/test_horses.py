import uuid

import pytest
from httpx import AsyncClient

from app.models.horse import Horse
from app.models.user import User


@pytest.mark.asyncio
class TestHorseCRUD:
    async def test_create_horse(self, client: AsyncClient, auth_headers: dict):
        response = await client.post("/api/v1/horses/", json={
            "name": "Storm",
            "breed": "Mustang",
            "age": 7,
            "temperament": "bold",
            "bio": "A bold mustang",
            "location_city": "Calgary",
            "location_country": "Canada",
        }, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Storm"
        assert data["breed"] == "Mustang"

    async def test_list_own_horses(
        self, client: AsyncClient, auth_headers: dict, test_horse: Horse
    ):
        response = await client.get("/api/v1/horses/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert any(h["id"] == str(test_horse.id) for h in data["items"])

    async def test_get_horse(
        self, client: AsyncClient, auth_headers: dict, test_horse: Horse
    ):
        response = await client.get(
            f"/api/v1/horses/{test_horse.id}", headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Thunder"

    async def test_update_horse(
        self, client: AsyncClient, auth_headers: dict, test_horse: Horse
    ):
        response = await client.patch(
            f"/api/v1/horses/{test_horse.id}",
            json={"name": "Thunder Updated"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Thunder Updated"

    async def test_delete_horse(
        self, client: AsyncClient, auth_headers: dict, test_horse: Horse
    ):
        response = await client.delete(
            f"/api/v1/horses/{test_horse.id}", headers=auth_headers
        )
        assert response.status_code == 204

    async def test_max_horses_limit(self, client: AsyncClient, auth_headers: dict):
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
