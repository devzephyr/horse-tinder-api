"""API6:2023 - Unrestricted Access to Sensitive Business Flows

Tests that business-critical flows have anti-automation protections:
daily swipe limits and message cooldowns.
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.models.horse import Horse
from app.models.match import Match
from app.models.user import User


@pytest.mark.asyncio
class TestSwipeLimit:
    async def test_daily_swipe_limit_enforced(
        self, client: AsyncClient, db: AsyncSession
    ):
        """After 100 swipes in a day, the 101st should be rejected."""
        user = User(
            id=uuid.uuid4(),
            email="swipeheavy@example.com",
            hashed_password=hash_password("SwipePass1!"),
            display_name="Heavy Swiper",
            role="user",
        )
        db.add(user)

        swiper_horse = Horse(
            id=uuid.uuid4(),
            owner_id=user.id,
            name="Swiper",
            breed="Arabian",
            age=5,
            temperament="spirited",
            location_city="Toronto",
            location_country="Canada",
        )
        db.add(swiper_horse)
        await db.flush()

        token = create_access_token(user.id, "user")
        headers = {"Authorization": f"Bearer {token}"}

        target_horses = []
        other = User(
            id=uuid.uuid4(),
            email="targetowner@example.com",
            hashed_password=hash_password("TargetPass1!"),
            display_name="Target Owner",
            role="user",
        )
        db.add(other)

        for i in range(101):
            h = Horse(
                id=uuid.uuid4(),
                owner_id=other.id,
                name=f"Target {i}",
                breed="Mustang",
                age=3,
                temperament="calm",
                location_city="Vancouver",
                location_country="Canada",
            )
            db.add(h)
            target_horses.append(h)
        await db.flush()

        for i in range(100):
            resp = await client.post("/api/v1/swipes/", json={
                "swiper_horse_id": str(swiper_horse.id),
                "swiped_horse_id": str(target_horses[i].id),
                "direction": "pass",
            }, headers=headers)
            assert resp.status_code == 201, f"Swipe {i+1} failed: {resp.json()}"

        resp = await client.post("/api/v1/swipes/", json={
            "swiper_horse_id": str(swiper_horse.id),
            "swiped_horse_id": str(target_horses[100].id),
            "direction": "pass",
        }, headers=headers)
        assert resp.status_code == 429


@pytest.mark.asyncio
class TestMessageCooldown:
    async def test_rapid_messages_throttled(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_match: Match,
    ):
        """Sending 2 messages within 1 second should throttle the second."""
        resp1 = await client.post(
            f"/api/v1/matches/{test_match.id}/messages/",
            json={"content": "Message 1"},
            headers=auth_headers,
        )
        assert resp1.status_code == 201

        resp2 = await client.post(
            f"/api/v1/matches/{test_match.id}/messages/",
            json={"content": "Message 2"},
            headers=auth_headers,
        )
        assert resp2.status_code == 429
