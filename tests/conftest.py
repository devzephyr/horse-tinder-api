import asyncio
import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.security import create_access_token, hash_password
from app.models.base import Base
from app.models.horse import Horse
from app.models.match import Match
from app.models.user import User

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
test_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    from app.core.rate_limiter import limiter
    limiter.reset()

    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    async with test_session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    from app.db.session import get_db
    from app.main import app

    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db: AsyncSession) -> User:
    user = User(
        id=uuid.uuid4(),
        email="testuser@example.com",
        hashed_password=hash_password("TestPass123!"),
        display_name="Test User",
        role="user",
    )
    db.add(user)
    await db.flush()
    return user


@pytest_asyncio.fixture
async def test_admin(db: AsyncSession) -> User:
    admin = User(
        id=uuid.uuid4(),
        email="admin@example.com",
        hashed_password=hash_password("AdminPass123!"),
        display_name="Admin User",
        role="admin",
    )
    db.add(admin)
    await db.flush()
    return admin


@pytest_asyncio.fixture
async def other_user(db: AsyncSession) -> User:
    user = User(
        id=uuid.uuid4(),
        email="otheruser@example.com",
        hashed_password=hash_password("OtherPass123!"),
        display_name="Other User",
        role="user",
    )
    db.add(user)
    await db.flush()
    return user


@pytest_asyncio.fixture
def user_token(test_user: User) -> str:
    return create_access_token(test_user.id, test_user.role)


@pytest_asyncio.fixture
def admin_token(test_admin: User) -> str:
    return create_access_token(test_admin.id, test_admin.role)


@pytest_asyncio.fixture
def other_user_token(other_user: User) -> str:
    return create_access_token(other_user.id, other_user.role)


@pytest_asyncio.fixture
def auth_headers(user_token: str) -> dict:
    return {"Authorization": f"Bearer {user_token}"}


@pytest_asyncio.fixture
def admin_headers(admin_token: str) -> dict:
    return {"Authorization": f"Bearer {admin_token}"}


@pytest_asyncio.fixture
def other_headers(other_user_token: str) -> dict:
    return {"Authorization": f"Bearer {other_user_token}"}


@pytest_asyncio.fixture
async def test_horse(db: AsyncSession, test_user: User) -> Horse:
    horse = Horse(
        id=uuid.uuid4(),
        owner_id=test_user.id,
        name="Thunder",
        breed="Arabian",
        age=5,
        temperament="spirited",
        bio="A spirited Arabian stallion",
        location_city="Toronto",
        location_state="Ontario",
        location_country="Canada",
    )
    db.add(horse)
    await db.flush()
    return horse


@pytest_asyncio.fixture
async def other_horse(db: AsyncSession, other_user: User) -> Horse:
    horse = Horse(
        id=uuid.uuid4(),
        owner_id=other_user.id,
        name="Lightning",
        breed="Thoroughbred",
        age=4,
        temperament="bold",
        bio="A bold Thoroughbred mare",
        location_city="Vancouver",
        location_state="BC",
        location_country="Canada",
    )
    db.add(horse)
    await db.flush()
    return horse


@pytest_asyncio.fixture
async def test_match(db: AsyncSession, test_horse: Horse, other_horse: Horse) -> Match:
    a_id, b_id = sorted([test_horse.id, other_horse.id])
    match = Match(
        id=uuid.uuid4(),
        horse_a_id=a_id,
        horse_b_id=b_id,
    )
    db.add(match)
    await db.flush()
    return match
