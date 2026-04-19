import pytest
from httpx import AsyncClient

from app.models.user import User


@pytest.mark.asyncio
class TestRegister:
    async def test_register_success(self, client: AsyncClient):
        response = await client.post("/api/v1/auth/register", json={
            "email": "new@example.com",
            "password": "SecurePass1!",
            "display_name": "New User",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "new@example.com"
        assert "hashed_password" not in data

    async def test_register_duplicate_email(self, client: AsyncClient, test_user: User):
        response = await client.post("/api/v1/auth/register", json={
            "email": test_user.email,
            "password": "SecurePass1!",
            "display_name": "Duplicate",
        })
        assert response.status_code == 409

    async def test_register_weak_password(self, client: AsyncClient):
        response = await client.post("/api/v1/auth/register", json={
            "email": "weak@example.com",
            "password": "weak",
            "display_name": "Weak",
        })
        assert response.status_code == 422


@pytest.mark.asyncio
class TestLogin:
    async def test_login_success(self, client: AsyncClient, test_user: User):
        response = await client.post("/api/v1/auth/login", json={
            "email": test_user.email,
            "password": "TestPass123!",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client: AsyncClient, test_user: User):
        response = await client.post("/api/v1/auth/login", json={
            "email": test_user.email,
            "password": "WrongPassword1!",
        })
        assert response.status_code == 401

    async def test_login_nonexistent_user(self, client: AsyncClient):
        response = await client.post("/api/v1/auth/login", json={
            "email": "nobody@example.com",
            "password": "SecurePass1!",
        })
        assert response.status_code == 401


@pytest.mark.asyncio
class TestRefresh:
    async def test_refresh_success(self, client: AsyncClient, test_user: User):
        login_resp = await client.post("/api/v1/auth/login", json={
            "email": test_user.email,
            "password": "TestPass123!",
        })
        refresh_token = login_resp.json()["refresh_token"]

        refresh_resp = await client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token,
        })
        assert refresh_resp.status_code == 200
        assert "access_token" in refresh_resp.json()

    async def test_refresh_invalid_token(self, client: AsyncClient):
        response = await client.post("/api/v1/auth/refresh", json={
            "refresh_token": "invalid-token",
        })
        assert response.status_code == 401

    async def test_refresh_token_rotation(self, client: AsyncClient, test_user: User):
        login_resp = await client.post("/api/v1/auth/login", json={
            "email": test_user.email,
            "password": "TestPass123!",
        })
        old_refresh = login_resp.json()["refresh_token"]

        refresh_resp = await client.post("/api/v1/auth/refresh", json={
            "refresh_token": old_refresh,
        })
        assert refresh_resp.status_code == 200

        reuse_resp = await client.post("/api/v1/auth/refresh", json={
            "refresh_token": old_refresh,
        })
        assert reuse_resp.status_code == 401


@pytest.mark.asyncio
class TestLogout:
    async def test_logout(self, client: AsyncClient, test_user: User, auth_headers: dict):
        login_resp = await client.post("/api/v1/auth/login", json={
            "email": test_user.email,
            "password": "TestPass123!",
        })
        refresh_token = login_resp.json()["refresh_token"]

        logout_resp = await client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": refresh_token},
            headers=auth_headers,
        )
        assert logout_resp.status_code == 204

        refresh_resp = await client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token,
        })
        assert refresh_resp.status_code == 401
