"""Repository invariants against the real database, including concurrency safety."""
from __future__ import annotations

import threading
from uuid import uuid4

import pytest

from apps.identity.domain import Email, RefreshToken, SingleUseToken, TokenReused, User
from apps.identity.infrastructure.repositories import (
    DjangoEmailVerificationRepository,
    DjangoRefreshTokenRepository,
    DjangoUserRepository,
)


@pytest.fixture
def users() -> DjangoUserRepository:
    return DjangoUserRepository()


@pytest.fixture
def refresh_tokens() -> DjangoRefreshTokenRepository:
    return DjangoRefreshTokenRepository()


@pytest.fixture
def email_tokens() -> DjangoEmailVerificationRepository:
    return DjangoEmailVerificationRepository()


@pytest.fixture
def persisted_user(users: DjangoUserRepository) -> User:
    user = User.register(
        email=Email("repo@example.com"), display_name="Repo", password_hash="hash"
    )
    users.add(user)
    return user


@pytest.mark.integration
@pytest.mark.django_db
class TestUserRepository:
    def test_round_trip(self, users: DjangoUserRepository) -> None:
        user = User.register(
            email=Email("a@b.com"), display_name="X", password_hash="hash"
        )
        users.add(user)
        loaded = users.get_by_email("a@b.com")
        assert loaded is not None
        assert loaded.id == user.id
        assert loaded.email.value == "a@b.com"


@pytest.mark.integration
@pytest.mark.django_db
class TestRefreshTokenRepository:
    def test_rotation_marks_old_used_and_inserts_new(
        self, persisted_user: User, refresh_tokens: DjangoRefreshTokenRepository
    ) -> None:
        old = RefreshToken.issue(user_id=persisted_user.id, token="old-token")
        refresh_tokens.add(old)
        new = RefreshToken.issue(
            user_id=persisted_user.id, token="new-token", family_id=old.family_id
        )
        refresh_tokens.rotate(old, new)
        reloaded_old = refresh_tokens.get_by_token("old-token")
        reloaded_new = refresh_tokens.get_by_token("new-token")
        assert reloaded_old is not None and reloaded_old.used_at is not None
        assert reloaded_new is not None and reloaded_new.used_at is None

    def test_concurrent_rotation_lets_only_one_winner(
        self, persisted_user: User, refresh_tokens: DjangoRefreshTokenRepository
    ) -> None:
        # Two threads attempting to rotate the same token simultaneously must produce
        # exactly one winner; the loser must see TokenReused. This is the core invariant
        # of refresh-token rotation under high concurrency (ADR-03, RULE-12).
        old = RefreshToken.issue(user_id=persisted_user.id, token="race-token")
        refresh_tokens.add(old)
        outcomes: list[str] = []
        barrier = threading.Barrier(2)

        def attempt(name: str) -> None:
            barrier.wait()
            new = RefreshToken.issue(
                user_id=persisted_user.id,
                token=f"new-{name}",
                family_id=old.family_id,
            )
            try:
                refresh_tokens.rotate(old, new)
                outcomes.append(f"{name}:win")
            except TokenReused:
                outcomes.append(f"{name}:reused")

        t1 = threading.Thread(target=attempt, args=("a",))
        t2 = threading.Thread(target=attempt, args=("b",))
        t1.start(); t2.start(); t1.join(); t2.join()
        wins = [o for o in outcomes if o.endswith(":win")]
        reuses = [o for o in outcomes if o.endswith(":reused")]
        assert len(wins) == 1
        assert len(reuses) == 1

    def test_invalidate_family_marks_all_active(
        self, persisted_user: User, refresh_tokens: DjangoRefreshTokenRepository
    ) -> None:
        family = uuid4()
        for n in range(3):
            refresh_tokens.add(
                RefreshToken.issue(
                    user_id=persisted_user.id, token=f"t{n}", family_id=family
                )
            )
        refresh_tokens.invalidate_family(family)
        for n in range(3):
            t = refresh_tokens.get_by_token(f"t{n}")
            assert t is not None and t.used_at is not None


@pytest.mark.integration
@pytest.mark.django_db
class TestSingleUseTokens:
    def test_consume_is_atomic(
        self,
        persisted_user: User,
        email_tokens: DjangoEmailVerificationRepository,
    ) -> None:
        tok = SingleUseToken.for_email_verification(
            user_id=persisted_user.id, token="single"
        )
        email_tokens.add(tok)
        first = email_tokens.consume("single")
        second = email_tokens.consume("single")
        assert first is not None
        assert second is None
