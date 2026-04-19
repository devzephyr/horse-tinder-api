import pytest
from httpx import AsyncClient

from app.models.horse import Horse
from app.models.user import User


@pytest.mark.asyncio
class TestSwipes:
    async def test_swipe_like(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_horse: Horse,
        other_horse: Horse,
    ):
        response = await client.post("/api/v1/swipes/", json={
            "swiper_horse_id": str(test_horse.id),
            "swiped_horse_id": str(other_horse.id),
            "direction": "like",
        }, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["swipe"]["direction"] == "like"

    async def test_swipe_pass(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_horse: Horse,
        other_horse: Horse,
    ):
        response = await client.post("/api/v1/swipes/", json={
            "swiper_horse_id": str(test_horse.id),
            "swiped_horse_id": str(other_horse.id),
            "direction": "pass",
        }, headers=auth_headers)
        assert response.status_code == 201

    async def test_duplicate_swipe_rejected(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_horse: Horse,
        other_horse: Horse,
    ):
        await client.post("/api/v1/swipes/", json={
            "swiper_horse_id": str(test_horse.id),
            "swiped_horse_id": str(other_horse.id),
            "direction": "like",
        }, headers=auth_headers)

        response = await client.post("/api/v1/swipes/", json={
            "swiper_horse_id": str(test_horse.id),
            "swiped_horse_id": str(other_horse.id),
            "direction": "pass",
        }, headers=auth_headers)
        assert response.status_code == 409

    async def test_cannot_swipe_own_horse(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_horse: Horse,
    ):
        response = await client.post("/api/v1/swipes/", json={
            "swiper_horse_id": str(test_horse.id),
            "swiped_horse_id": str(test_horse.id),
            "direction": "like",
        }, headers=auth_headers)
        assert response.status_code == 422

    async def test_remaining_swipes(
        self, client: AsyncClient, auth_headers: dict
    ):
        response = await client.get("/api/v1/swipes/remaining", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["limit"] == 100


@pytest.mark.asyncio
class TestMatchCreation:
    async def test_mutual_like_creates_match(
        self,
        client: AsyncClient,
        auth_headers: dict,
        other_headers: dict,
        test_horse: Horse,
        other_horse: Horse,
    ):
        await client.post("/api/v1/swipes/", json={
            "swiper_horse_id": str(test_horse.id),
            "swiped_horse_id": str(other_horse.id),
            "direction": "like",
        }, headers=auth_headers)

        response = await client.post("/api/v1/swipes/", json={
            "swiper_horse_id": str(other_horse.id),
            "swiped_horse_id": str(test_horse.id),
            "direction": "like",
        }, headers=other_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["is_match"] is True
        assert data["match_id"] is not None
