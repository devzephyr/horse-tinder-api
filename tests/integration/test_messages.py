import pytest
from httpx import AsyncClient

from app.models.match import Match
from app.models.user import User


@pytest.mark.asyncio
class TestMessages:
    async def test_send_message(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_match: Match,
    ):
        response = await client.post(
            f"/api/v1/matches/{test_match.id}/messages/",
            json={"content": "Hello!"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        assert response.json()["content"] == "Hello!"

    async def test_list_messages(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_match: Match,
    ):
        await client.post(
            f"/api/v1/matches/{test_match.id}/messages/",
            json={"content": "First message"},
            headers=auth_headers,
        )

        response = await client.get(
            f"/api/v1/matches/{test_match.id}/messages/",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    async def test_message_too_long(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_match: Match,
    ):
        response = await client.post(
            f"/api/v1/matches/{test_match.id}/messages/",
            json={"content": "x" * 2001},
            headers=auth_headers,
        )
        assert response.status_code == 422

    async def test_empty_message_rejected(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_match: Match,
    ):
        response = await client.post(
            f"/api/v1/matches/{test_match.id}/messages/",
            json={"content": ""},
            headers=auth_headers,
        )
        assert response.status_code == 422
