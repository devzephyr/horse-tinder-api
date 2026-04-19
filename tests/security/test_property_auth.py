"""API3:2023 - Broken Object Property Level Authorization

Tests that clients cannot set admin-only properties (mass assignment)
and that sensitive fields are never exposed in API responses.
"""

import pytest
from httpx import AsyncClient

from app.models.user import User


@pytest.mark.asyncio
class TestMassAssignment:
    async def test_register_cannot_set_role(self, client: AsyncClient):
        """Registering with role='admin' must be ignored -- user gets 'user' role."""
        response = await client.post("/api/v1/auth/register", json={
            "email": "attacker@example.com",
            "password": "SecurePass1!",
            "display_name": "Attacker",
            "role": "admin",
        })
        assert response.status_code == 201

        login_resp = await client.post("/api/v1/auth/login", json={
            "email": "attacker@example.com",
            "password": "SecurePass1!",
        })
        token = login_resp.json()["access_token"]

        me_resp = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_resp.status_code == 200
        assert "role" not in me_resp.json()

        admin_resp = await client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert admin_resp.status_code == 403

    async def test_horse_create_cannot_set_owner_id(
        self, client: AsyncClient, auth_headers: dict, other_user: User
    ):
        """Creating a horse with another user's owner_id must be ignored."""
        response = await client.post("/api/v1/horses/", json={
            "name": "Stolen",
            "breed": "Arabian",
            "age": 5,
            "temperament": "calm",
            "location_city": "Toronto",
            "location_country": "Canada",
            "owner_id": str(other_user.id),
        }, headers=auth_headers)
        assert response.status_code == 201
        assert response.json()["owner_id"] != str(other_user.id)

    async def test_horse_create_cannot_set_is_active(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Creating a horse with is_active=False must be ignored."""
        response = await client.post("/api/v1/horses/", json={
            "name": "Hidden",
            "breed": "Arabian",
            "age": 5,
            "temperament": "calm",
            "location_city": "Toronto",
            "location_country": "Canada",
            "is_active": False,
        }, headers=auth_headers)
        assert response.status_code == 201
        assert response.json()["is_active"] is True


@pytest.mark.asyncio
class TestSensitiveDataExposure:
    async def test_user_me_excludes_password(
        self, client: AsyncClient, auth_headers: dict
    ):
        """GET /users/me must never return hashed_password."""
        response = await client.get("/api/v1/users/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "hashed_password" not in data
        assert "password" not in data

    async def test_register_response_excludes_password(self, client: AsyncClient):
        """POST /register response must not contain the password hash."""
        response = await client.post("/api/v1/auth/register", json={
            "email": "nopassleak@example.com",
            "password": "SecurePass1!",
            "display_name": "No Leak",
        })
        assert response.status_code == 201
        data = response.json()
        assert "hashed_password" not in data
        assert "password" not in data

    async def test_user_me_excludes_internal_fields(
        self, client: AsyncClient, auth_headers: dict
    ):
        """GET /users/me must not expose is_locked, failed_login_attempts."""
        response = await client.get("/api/v1/users/me", headers=auth_headers)
        data = response.json()
        assert "is_locked" not in data
        assert "failed_login_attempts" not in data
        assert "locked_until" not in data

    async def test_admin_view_has_extra_fields(
        self, client: AsyncClient, admin_headers: dict, test_user: User
    ):
        """Admin GET /admin/users/{id} should show role and lock status."""
        response = await client.get(
            f"/api/v1/admin/users/{test_user.id}", headers=admin_headers
        )
        data = response.json()
        assert "role" in data
        assert "is_locked" in data
        assert "hashed_password" not in data
