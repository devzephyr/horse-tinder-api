from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import ConflictException, RateLimitException, UnauthorizedException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.user import LoginAttempt, RefreshToken, User
from app.schemas.auth import RegisterRequest, TokenResponse

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 30


async def register(db: AsyncSession, data: RegisterRequest) -> User:
    existing = (
        await db.execute(select(User).where(User.email == data.email.lower()))
    ).scalar_one_or_none()

    if existing:
        raise ConflictException("Email already registered")

    user = User(
        email=data.email.lower(),
        hashed_password=hash_password(data.password),
        display_name=data.display_name,
        role="user",
    )
    db.add(user)
    await db.flush()
    return user


async def login(
    db: AsyncSession, email: str, password: str, ip_address: str
) -> TokenResponse:
    user = (
        await db.execute(select(User).where(User.email == email.lower()))
    ).scalar_one_or_none()

    if user and user.is_locked:
        if user.locked_until and user.locked_until > datetime.now(timezone.utc):
            _log_attempt(db, email, ip_address, success=False)
            raise RateLimitException("Account is temporarily locked. Try again later.")
        else:
            user.is_locked = False
            user.failed_login_attempts = 0
            user.locked_until = None

    if not user or not user.is_active or not verify_password(password, user.hashed_password):
        if user:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
                user.is_locked = True
                user.locked_until = datetime.now(timezone.utc) + timedelta(
                    minutes=LOCKOUT_DURATION_MINUTES
                )
        _log_attempt(db, email, ip_address, success=False)
        raise UnauthorizedException("Invalid email or password")

    user.failed_login_attempts = 0
    _log_attempt(db, email, ip_address, success=True)

    access_token = create_access_token(user.id, user.role)
    refresh_token = create_refresh_token(user.id)

    db.add(RefreshToken(
        user_id=user.id,
        token_hash=hash_token(refresh_token),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    ))
    await db.flush()

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


async def refresh_tokens(db: AsyncSession, refresh_token_str: str) -> TokenResponse:
    try:
        payload = decode_refresh_token(refresh_token_str)
    except Exception as exc:
        raise UnauthorizedException("Invalid or expired refresh token") from exc

    token_hash = hash_token(refresh_token_str)
    stored_token = (
        await db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked == False,  # noqa: E712
                RefreshToken.expires_at > datetime.now(timezone.utc),
            )
        )
    ).scalar_one_or_none()

    if not stored_token:
        raise UnauthorizedException("Invalid or expired refresh token")

    stored_token.revoked = True

    user = (await db.execute(select(User).where(User.id == stored_token.user_id))).scalar_one()

    new_access = create_access_token(user.id, user.role)
    new_refresh = create_refresh_token(user.id)

    db.add(RefreshToken(
        user_id=user.id,
        token_hash=hash_token(new_refresh),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    ))
    await db.flush()

    return TokenResponse(access_token=new_access, refresh_token=new_refresh)


async def logout(db: AsyncSession, refresh_token_str: str) -> None:
    token_hash = hash_token(refresh_token_str)
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.token_hash == token_hash)
        .values(revoked=True)
    )


def _log_attempt(db: AsyncSession, email: str, ip_address: str, success: bool) -> None:
    db.add(LoginAttempt(email=email.lower(), ip_address=ip_address, success=success))
