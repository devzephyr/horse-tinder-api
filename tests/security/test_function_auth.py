"""API5:2023 - Broken Function Level Authorization

Tests that regular users cannot access admin endpoints,
and unauthenticated users get 401 (not 403 or 200).
"""

import pytest
from httpx import AsyncClient

from app.models.user import User


@pytest.mark.asyncio
class TestFunctionLevelAuth:
    async def test_regular_user_cannot_list_users(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Regular user hitting /admin/users should get 403."""
        response = await client.get("/api/v1/admin/users", headers=auth_headers)
        assert response.status_code == 403

    async def test_regular_user_cannot_get_user(
        self, client: AsyncClient, auth_headers: dict, test_user: User
    ):
        """Regular user hitting /admin/users/{id} should get 403."""
        response = await client.get(
            f"/api/v1/admin/users/{test_user.id}", headers=auth_headers
        )
        assert response.status_code == 403

    async def test_regular_user_cannot_update_user(
        self, client: AsyncClient, auth_headers: dict, test_user: User
    ):
        """Regular user trying to promote themselves via admin endpoint should get 403."""
        response = await client.patch(
            f"/api/v1/admin/users/{test_user.id}",
            json={"role": "admin"},
            headers=auth_headers,
        )
        assert response.status_code == 403

    async def test_regular_user_cannot_delete_user(
        self, client: AsyncClient, auth_headers: dict, other_user: User
    ):
        """Regular user hitting admin delete should get 403."""
        response = await client.delete(
            f"/api/v1/admin/users/{other_user.id}", headers=auth_headers
        )
        assert response.status_code == 403

    async def test_regular_user_cannot_list_all_horses(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Regular user hitting /admin/horses should get 403."""
        response = await client.get("/api/v1/admin/horses", headers=auth_headers)
        assert response.status_code == 403

    async def test_regular_user_cannot_moderate_horse(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Regular user hitting admin horse moderation should get 403."""
        import uuid

        response = await client.patch(
            f"/api/v1/admin/horses/{uuid.uuid4()}",
            json={"is_active": False},
            headers=auth_headers,
        )
        assert response.status_code == 403

    async def test_unauthenticated_admin_gets_401(self, client: AsyncClient):
        """No token on admin endpoint should get 401, not 403."""
        response = await client.get("/api/v1/admin/users")
        assert response.status_code == 401

    async def test_admin_can_access(
        self, client: AsyncClient, admin_headers: dict
    ):
        """Admin user should successfully access admin endpoints."""
        response = await client.get("/api/v1/admin/users", headers=admin_headers)
        assert response.status_code == 200
