"""API2:2023 - Broken Authentication

Tests for brute force protection, token manipulation, account lockout,
and proper token lifecycle management.
"""

import uuid

import jwt
import pytest
from httpx import AsyncClient

from app.core.config import settings
from app.core.security import ALGORITHM
from app.models.user import User


@pytest.mark.asyncio
class TestBruteForce:
    async def test_account_lockout_after_failures(
        self, client: AsyncClient, test_user: User
    ):
        """5 consecutive failed logins should lock the account."""
        for i in range(5):
            resp = await client.post("/api/v1/auth/login", json={
                "email": test_user.email,
                "password": f"WrongPass{i}!",
            })
            assert resp.status_code == 401

        resp = await client.post("/api/v1/auth/login", json={
            "email": test_user.email,
            "password": "TestPass123!",
        })
        assert resp.status_code == 429


@pytest.mark.asyncio
class TestTokenManipulation:
    async def test_expired_access_token(self, client: AsyncClient, test_user: User):
        """Expired access token should return 401."""
        from datetime import datetime, timedelta, timezone

        payload = {
            "sub": str(test_user.id),
            "role": "user",
            "type": "access",
            "iat": datetime.now(timezone.utc) - timedelta(hours=2),
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
        }
        expired_token = jwt.encode(payload, settings.ACCESS_TOKEN_SECRET, algorithm=ALGORITHM)

        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert response.status_code == 401

    async def test_forged_token_wrong_secret(self, client: AsyncClient):
        """Token signed with wrong secret should return 401."""
        payload = {
            "sub": str(uuid.uuid4()),
            "role": "admin",
            "type": "access",
        }
        forged_token = jwt.encode(payload, "wrong-secret-that-is-at-least-32-bytes-long", algorithm=ALGORITHM)

        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {forged_token}"},
        )
        assert response.status_code == 401

    async def test_refresh_token_cannot_access_api(
        self, client: AsyncClient, test_user: User
    ):
        """A refresh token used as an access token should be rejected."""
        from app.core.security import create_refresh_token

        refresh = create_refresh_token(test_user.id)
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {refresh}"},
        )
        assert response.status_code == 401

    async def test_no_token(self, client: AsyncClient):
        """No Authorization header should return 401."""
        response = await client.get("/api/v1/users/me")
        assert response.status_code == 401

    async def test_malformed_bearer(self, client: AsyncClient):
        """Malformed Authorization header should return 401."""
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": "NotBearer token"},
        )
        assert response.status_code == 401

    async def test_token_for_nonexistent_user(self, client: AsyncClient):
        """Token with valid signature but non-existent user ID should return 401."""
        from app.core.security import create_access_token

        fake_id = uuid.uuid4()
        token = create_access_token(fake_id, "user")
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401
