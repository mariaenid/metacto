"""Vote repository against the real database, including concurrency safety."""

from __future__ import annotations

import threading

import pytest

from apps.feature_requests.domain import Description, FeatureRequest, Title
from apps.feature_requests.infrastructure.models import FeatureRequestRecord, VoteRecord
from apps.feature_requests.infrastructure.repositories import (
    DjangoFeatureRequestRepository,
)
from apps.feature_requests.infrastructure.vote_repository import DjangoVoteRepository
from apps.identity.domain import Email, User
from apps.identity.infrastructure.repositories import DjangoUserRepository


@pytest.fixture
def author():
    users = DjangoUserRepository()
    user = User.register(
        email=Email("vote-author@example.com"), display_name="VA", password_hash="h"
    )
    users.add(user)
    return user


@pytest.fixture
def feature_request(author) -> FeatureRequest:
    fr = FeatureRequest.submit(
        title=Title("vote me"), description=Description(""), author_id=author.id
    )
    DjangoFeatureRequestRepository().submit_with_author_vote(fr)
    return fr


@pytest.fixture
def repo() -> DjangoVoteRepository:
    return DjangoVoteRepository()


def _make_voter(suffix: str):
    users = DjangoUserRepository()
    u = User.register(
        email=Email(f"voter{suffix}@example.com"), display_name=f"V{suffix}", password_hash="h"
    )
    users.add(u)
    return u


@pytest.mark.integration
@pytest.mark.django_db
class TestCast:
    def test_first_vote_increments_count(self, feature_request, repo) -> None:
        voter = _make_voter("1")
        result = repo.cast(feature_request_id=feature_request.id, user_id=voter.id)
        assert result.voted is True
        assert result.vote_count == 2  # author + voter

    def test_duplicate_vote_is_idempotent(self, feature_request, repo) -> None:
        voter = _make_voter("2")
        first = repo.cast(feature_request_id=feature_request.id, user_id=voter.id)
        second = repo.cast(feature_request_id=feature_request.id, user_id=voter.id)
        assert first.vote_count == second.vote_count == 2
        assert (
            VoteRecord.objects.filter(
                feature_request_id=feature_request.id, user_id=voter.id
            ).count()
            == 1
        )

    @pytest.mark.django_db(transaction=True)
    def test_concurrent_first_vote_counts_exactly_once(self, feature_request, repo) -> None:
        # Two threads casting the same user's first vote on the same request must produce
        # exactly one Vote row and a single increment on vote_count (ADR-03, RULE-01).
        voter = _make_voter("race")
        results = []

        def attempt() -> None:
            results.append(repo.cast(feature_request_id=feature_request.id, user_id=voter.id))

        threads = [threading.Thread(target=attempt) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert (
            VoteRecord.objects.filter(
                feature_request_id=feature_request.id, user_id=voter.id
            ).count()
            == 1
        )
        FeatureRequestRecord.objects.filter(id=feature_request.id).update()
        final = FeatureRequestRecord.objects.get(id=feature_request.id).vote_count
        assert final == 2  # author implicit + this voter exactly once


@pytest.mark.integration
@pytest.mark.django_db
class TestRetract:
    def test_retract_decrements_when_present(self, feature_request, repo) -> None:
        voter = _make_voter("r1")
        repo.cast(feature_request_id=feature_request.id, user_id=voter.id)
        result = repo.retract(feature_request_id=feature_request.id, user_id=voter.id)
        assert result.voted is False
        assert result.vote_count == 1

    def test_retract_is_idempotent_when_absent(self, feature_request, repo) -> None:
        stranger = _make_voter("r2")
        first = repo.retract(feature_request_id=feature_request.id, user_id=stranger.id)
        second = repo.retract(feature_request_id=feature_request.id, user_id=stranger.id)
        assert first.vote_count == second.vote_count == 1
