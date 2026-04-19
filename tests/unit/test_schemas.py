import uuid
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.auth import RegisterRequest
from app.schemas.horse import HorseCreate, TemperamentEnum
from app.schemas.pagination import PaginationParams
from app.schemas.user import UserRead


class TestRegisterSchema:
    def test_valid_registration(self):
        data = RegisterRequest(
            email="test@example.com",
            password="SecurePass1!",
            display_name="Test User",
        )
        assert data.email == "test@example.com"

    def test_password_too_short(self):
        with pytest.raises(ValidationError):
            RegisterRequest(
                email="test@example.com",
                password="Short1!",
                display_name="Test",
            )

    def test_password_no_uppercase(self):
        with pytest.raises(ValidationError):
            RegisterRequest(
                email="test@example.com",
                password="nouppercase1!",
                display_name="Test",
            )

    def test_password_no_lowercase(self):
        with pytest.raises(ValidationError):
            RegisterRequest(
                email="test@example.com",
                password="NOLOWERCASE1!",
                display_name="Test",
            )

    def test_password_no_digit(self):
        with pytest.raises(ValidationError):
            RegisterRequest(
                email="test@example.com",
                password="NoDigitHere!!",
                display_name="Test",
            )

    def test_password_no_special(self):
        with pytest.raises(ValidationError):
            RegisterRequest(
                email="test@example.com",
                password="NoSpecial123",
                display_name="Test",
            )

    def test_invalid_email(self):
        with pytest.raises(ValidationError):
            RegisterRequest(
                email="not-an-email",
                password="SecurePass1!",
                display_name="Test",
            )

    def test_display_name_too_short(self):
        with pytest.raises(ValidationError):
            RegisterRequest(
                email="test@example.com",
                password="SecurePass1!",
                display_name="T",
            )


class TestUserReadSchema:
    """API3: Verify sensitive fields are excluded from UserRead."""

    def test_excludes_hashed_password(self):
        fields = UserRead.model_fields
        assert "hashed_password" not in fields

    def test_excludes_role(self):
        fields = UserRead.model_fields
        assert "role" not in fields

    def test_excludes_is_locked(self):
        fields = UserRead.model_fields
        assert "is_locked" not in fields

    def test_excludes_failed_login_attempts(self):
        fields = UserRead.model_fields
        assert "failed_login_attempts" not in fields


class TestHorseCreateSchema:
    """API3: Verify owner_id and is_active cannot be set by client."""

    def test_no_owner_id_field(self):
        fields = HorseCreate.model_fields
        assert "owner_id" not in fields

    def test_no_is_active_field(self):
        fields = HorseCreate.model_fields
        assert "is_active" not in fields

    def test_no_id_field(self):
        fields = HorseCreate.model_fields
        assert "id" not in fields

    def test_valid_horse(self):
        horse = HorseCreate(
            name="Thunder",
            breed="Arabian",
            age=5,
            temperament=TemperamentEnum.SPIRITED,
            location_city="Toronto",
            location_country="Canada",
        )
        assert horse.name == "Thunder"

    def test_age_too_high(self):
        with pytest.raises(ValidationError):
            HorseCreate(
                name="Old",
                breed="Arabian",
                age=51,
                temperament=TemperamentEnum.CALM,
                location_city="Toronto",
                location_country="Canada",
            )

    def test_invalid_temperament(self):
        with pytest.raises(ValidationError):
            HorseCreate(
                name="Horse",
                breed="Arabian",
                age=5,
                temperament="aggressive",
                location_city="Toronto",
                location_country="Canada",
            )


class TestPaginationParams:
    """API4: Verify page_size is capped."""

    def test_default_values(self):
        params = PaginationParams()
        assert params.page == 1
        assert params.page_size == 20

    def test_max_page_size(self):
        with pytest.raises(ValidationError):
            PaginationParams(page_size=1000)

    def test_page_size_50_allowed(self):
        params = PaginationParams(page_size=50)
        assert params.page_size == 50

    def test_page_size_0_rejected(self):
        with pytest.raises(ValidationError):
            PaginationParams(page_size=0)
