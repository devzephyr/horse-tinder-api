import pytest
from httpx import AsyncClient

from app.models.user import User


@pytest.mark.asyncio
class TestAdminEndpoints:
    async def test_admin_list_users(
        self, client: AsyncClient, admin_headers: dict, test_user: User
    ):
        response = await client.get("/api/v1/admin/users", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    async def test_admin_get_user(
        self, client: AsyncClient, admin_headers: dict, test_user: User
    ):
        response = await client.get(
            f"/api/v1/admin/users/{test_user.id}", headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "user"
        assert "is_locked" in data
        assert "failed_login_attempts" in data

    async def test_admin_update_user(
        self, client: AsyncClient, admin_headers: dict, test_user: User
    ):
        response = await client.patch(
            f"/api/v1/admin/users/{test_user.id}",
            json={"is_active": False},
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["is_active"] is False

    async def test_admin_list_horses(
        self, client: AsyncClient, admin_headers: dict
    ):
        response = await client.get("/api/v1/admin/horses", headers=admin_headers)
        assert response.status_code == 200

    async def test_non_admin_rejected(
        self, client: AsyncClient, auth_headers: dict
    ):
        response = await client.get("/api/v1/admin/users", headers=auth_headers)
        assert response.status_code == 403
