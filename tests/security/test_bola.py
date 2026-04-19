"""API1:2023 - Broken Object Level Authorization (BOLA)

Tests that users cannot access, modify, or delete resources belonging to other users.
All unauthorized access attempts should return 404 (not 403) to prevent information leakage.
"""

import uuid

import pytest
from httpx import AsyncClient

from app.models.horse import Horse
from app.models.match import Match
from app.models.notification import Notification
from app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
class TestBOLA:
    async def test_cannot_update_other_users_horse(
        self,
        client: AsyncClient,
        auth_headers: dict,
        other_horse: Horse,
    ):
        """User A tries to PATCH User B's horse -- must get 404."""
        response = await client.patch(
            f"/api/v1/horses/{other_horse.id}",
            json={"name": "Stolen Horse"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_cannot_delete_other_users_horse(
        self,
        client: AsyncClient,
        auth_headers: dict,
        other_horse: Horse,
    ):
        """User A tries to DELETE User B's horse -- must get 404."""
        response = await client.delete(
            f"/api/v1/horses/{other_horse.id}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_cannot_add_photo_to_other_users_horse(
        self,
        client: AsyncClient,
        auth_headers: dict,
        other_horse: Horse,
    ):
        """User A tries to add a photo to User B's horse -- must get 404."""
        response = await client.post(
            f"/api/v1/horses/{other_horse.id}/photos/",
            json={"url": "https://i.imgur.com/test.jpg"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_cannot_read_messages_from_unrelated_match(
        self,
        client: AsyncClient,
        test_match: Match,
        db: AsyncSession,
    ):
        """A third user (not part of the match) tries to read messages -- must get 404."""
        bystander = User(
            id=uuid.uuid4(),
            email="bystander@example.com",
            hashed_password="$2b$12$fakehash",
            display_name="Bystander",
            role="user",
        )
        db.add(bystander)
        await db.flush()

        from app.core.security import create_access_token

        token = create_access_token(bystander.id, "user")
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.get(
            f"/api/v1/matches/{test_match.id}/messages/",
            headers=headers,
        )
        assert response.status_code == 404

    async def test_cannot_send_message_to_unrelated_match(
        self,
        client: AsyncClient,
        test_match: Match,
        db: AsyncSession,
    ):
        """A third user tries to send a message into someone else's match -- must get 404."""
        bystander = User(
            id=uuid.uuid4(),
            email="bystander2@example.com",
            hashed_password="$2b$12$fakehash",
            display_name="Bystander 2",
            role="user",
        )
        db.add(bystander)
        await db.flush()

        from app.core.security import create_access_token

        token = create_access_token(bystander.id, "user")
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post(
            f"/api/v1/matches/{test_match.id}/messages/",
            json={"content": "Hello from an attacker"},
            headers=headers,
        )
        assert response.status_code == 404

    async def test_cannot_access_nonexistent_horse(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Accessing a random UUID returns 404, not 500 or info leak."""
        fake_id = uuid.uuid4()
        response = await client.get(
            f"/api/v1/horses/{fake_id}", headers=auth_headers
        )
        assert response.status_code == 404

    async def test_cannot_read_other_users_notifications(
        self,
        client: AsyncClient,
        auth_headers: dict,
        other_user: User,
        db: AsyncSession,
    ):
        """User A tries to mark User B's notification as read -- must get 404."""
        notification = Notification(
            id=uuid.uuid4(),
            user_id=other_user.id,
            type="new_match",
            title="Test",
        )
        db.add(notification)
        await db.flush()

        response = await client.patch(
            f"/api/v1/notifications/{notification.id}/read",
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_swipe_with_unowned_horse(
        self,
        client: AsyncClient,
        auth_headers: dict,
        other_horse: Horse,
        test_horse: Horse,
    ):
        """User A tries to swipe using User B's horse as the swiper -- must get 404."""
        response = await client.post("/api/v1/swipes/", json={
            "swiper_horse_id": str(other_horse.id),
            "swiped_horse_id": str(test_horse.id),
            "direction": "like",
        }, headers=auth_headers)
        assert response.status_code == 404
