import uuid

import jwt
import pytest

from app.core.config import settings
from app.core.security import (
    ALGORITHM,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)


class TestPasswordHashing:
    def test_hash_and_verify(self):
        password = "SecurePass123!"
        hashed = hash_password(password)
        assert hashed != password
        assert verify_password(password, hashed)

    def test_wrong_password(self):
        hashed = hash_password("SecurePass123!")
        assert not verify_password("WrongPass123!", hashed)

    def test_different_hashes(self):
        password = "SecurePass123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        assert hash1 != hash2  # bcrypt uses random salt


class TestAccessToken:
    def test_create_and_decode(self):
        user_id = uuid.uuid4()
        token = create_access_token(user_id, "user")
        payload = decode_access_token(token)
        assert payload["sub"] == str(user_id)
        assert payload["role"] == "user"
        assert payload["type"] == "access"

    def test_admin_role(self):
        user_id = uuid.uuid4()
        token = create_access_token(user_id, "admin")
        payload = decode_access_token(token)
        assert payload["role"] == "admin"

    def test_invalid_token(self):
        with pytest.raises(jwt.InvalidTokenError):
            decode_access_token("invalid.token.here")

    def test_wrong_secret(self):
        user_id = uuid.uuid4()
        token = jwt.encode(
            {"sub": str(user_id), "type": "access"},
            "wrong-secret-that-is-at-least-32-bytes-long",
            algorithm=ALGORITHM,
        )
        with pytest.raises(jwt.InvalidSignatureError):
            decode_access_token(token)

    def test_expired_token(self):
        from datetime import datetime, timedelta, timezone

        payload = {
            "sub": str(uuid.uuid4()),
            "role": "user",
            "type": "access",
            "iat": datetime.now(timezone.utc) - timedelta(hours=2),
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
        }
        token = jwt.encode(payload, settings.ACCESS_TOKEN_SECRET, algorithm=ALGORITHM)
        with pytest.raises(jwt.ExpiredSignatureError):
            decode_access_token(token)

    def test_refresh_token_rejected_as_access(self):
        user_id = uuid.uuid4()
        refresh = create_refresh_token(user_id)
        with pytest.raises(jwt.InvalidTokenError):
            decode_access_token(refresh)


class TestRefreshToken:
    def test_create_and_decode(self):
        user_id = uuid.uuid4()
        token = create_refresh_token(user_id)
        payload = decode_refresh_token(token)
        assert payload["sub"] == str(user_id)
        assert payload["type"] == "refresh"

    def test_access_token_rejected_as_refresh(self):
        user_id = uuid.uuid4()
        access = create_access_token(user_id, "user")
        with pytest.raises(jwt.InvalidTokenError):
            decode_refresh_token(access)


class TestTokenHash:
    def test_consistent_hash(self):
        token = "some-token-value"
        assert hash_token(token) == hash_token(token)

    def test_different_tokens_different_hashes(self):
        assert hash_token("token1") != hash_token("token2")
