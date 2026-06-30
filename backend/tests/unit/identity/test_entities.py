"""Domain entity behaviour, including time-based invariants."""

from datetime import timedelta
from uuid import uuid4

import pytest

from apps.identity.domain import Email, RefreshToken, Role, SingleUseToken, User


@pytest.mark.unit
class TestUser:
    def test_register_initialises_safely(self) -> None:
        u = User.register(email=Email("a@b.com"), display_name="  Maria ", password_hash="x")
        assert u.email_verified is False
        assert u.role is Role.USER
        assert u.display_name == "Maria"
        assert u.can_write() is False
        assert u.can_moderate() is False

    def test_can_write_requires_verified_email(self) -> None:
        u = User.register(email=Email("a@b.com"), display_name="m", password_hash="x")
        u.mark_email_verified()
        assert u.can_write() is True

    def test_moderator_and_admin_can_moderate(self) -> None:
        u = User.register(email=Email("a@b.com"), display_name="m", password_hash="x")
        u.role = Role.MODERATOR
        assert u.can_moderate() is True
        u.role = Role.ADMIN
        assert u.can_moderate() is True


@pytest.mark.unit
class TestRefreshToken:
    def test_issued_token_is_active(self) -> None:
        t = RefreshToken.issue(user_id=uuid4(), token="abc")
        assert t.is_active() is True

    def test_used_token_is_not_active(self) -> None:
        t = RefreshToken.issue(user_id=uuid4(), token="abc")
        t.mark_used()
        assert t.is_active() is False

    def test_expired_token_is_not_active(self) -> None:
        t = RefreshToken.issue(user_id=uuid4(), token="abc")
        t.expires_at -= timedelta(days=31)
        assert t.is_active() is False


@pytest.mark.unit
class TestSingleUseToken:
    def test_email_verification_expiry_is_24h(self) -> None:
        t = SingleUseToken.for_email_verification(user_id=uuid4(), token="abc")
        delta = t.expires_at - t.created_at
        assert timedelta(hours=23) < delta < timedelta(hours=25)

    def test_password_reset_expiry_is_1h(self) -> None:
        t = SingleUseToken.for_password_reset(user_id=uuid4(), token="abc")
        delta = t.expires_at - t.created_at
        assert timedelta(minutes=59) < delta < timedelta(minutes=61)
