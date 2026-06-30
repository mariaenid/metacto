"""Vote use cases with in-memory fakes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4

import pytest

from apps.feature_requests.application import (
    FeatureRequestServices,
    VoteResult,
    cast_vote,
    retract_vote,
    submit_feature_request,
)
from apps.feature_requests.domain import (
    FeatureRequest,
    FeatureRequestNotFound,
    SortOption,
)


@dataclass(slots=True)
class _Repo:
    by_id: dict[UUID, FeatureRequest] = field(default_factory=dict)

    def submit_with_author_vote(self, fr: FeatureRequest) -> None:
        self.by_id[fr.id] = fr

    def get_by_id(self, request_id: UUID) -> FeatureRequest | None:
        return self.by_id.get(request_id)

    def list(self, *, sort: SortOption, limit: int, offset: int):  # pragma: no cover
        raise NotImplementedError


@dataclass(slots=True)
class _VoteRepo:
    voters: dict[UUID, set[UUID]] = field(default_factory=dict)
    counts: dict[UUID, int] = field(default_factory=dict)

    def cast(self, *, feature_request_id: UUID, user_id: UUID) -> VoteResult:
        voters = self.voters.setdefault(feature_request_id, set())
        if user_id not in voters:
            voters.add(user_id)
            self.counts[feature_request_id] = self.counts.get(feature_request_id, 0) + 1
        return VoteResult(
            feature_request_id=feature_request_id,
            voted=True,
            vote_count=self.counts.get(feature_request_id, 0),
        )

    def retract(self, *, feature_request_id: UUID, user_id: UUID) -> VoteResult:
        voters = self.voters.setdefault(feature_request_id, set())
        if user_id in voters:
            voters.remove(user_id)
            self.counts[feature_request_id] = max(self.counts.get(feature_request_id, 0) - 1, 0)
        return VoteResult(
            feature_request_id=feature_request_id,
            voted=False,
            vote_count=self.counts.get(feature_request_id, 0),
        )


@dataclass(slots=True)
class _Idem:
    store: dict[str, Any] = field(default_factory=dict)

    def get(self, key: str) -> Any | None:
        return self.store.get(key)

    def put(self, key: str, value: Any) -> None:
        self.store[key] = value


@pytest.fixture
def services() -> FeatureRequestServices:
    return FeatureRequestServices(requests=_Repo(), votes=_VoteRepo(), idempotency=_Idem())


def _seed(services: FeatureRequestServices, author: UUID) -> FeatureRequest:
    return submit_feature_request(services, title="Dark mode", description="", author_id=author)


@pytest.mark.unit
class TestCastVote:
    def test_first_cast_increments(self, services: FeatureRequestServices) -> None:
        author = uuid4()
        fr = _seed(services, author)
        # author already implicitly counted via _Repo? Our fake _VoteRepo starts at 0; reflect.
        services.votes.counts[fr.id] = fr.vote_count  # type: ignore[attr-defined]
        services.votes.voters[fr.id] = {author}  # type: ignore[attr-defined]
        voter = uuid4()
        result = cast_vote(services, feature_request_id=fr.id, user_id=voter)
        assert result.voted is True
        assert result.vote_count == 2

    def test_repeated_cast_is_idempotent(self, services: FeatureRequestServices) -> None:
        author = uuid4()
        fr = _seed(services, author)
        services.votes.counts[fr.id] = 1  # type: ignore[attr-defined]
        services.votes.voters[fr.id] = {author}  # type: ignore[attr-defined]
        voter = uuid4()
        first = cast_vote(services, feature_request_id=fr.id, user_id=voter)
        second = cast_vote(services, feature_request_id=fr.id, user_id=voter)
        assert first.vote_count == second.vote_count

    def test_unknown_request_raises(self, services: FeatureRequestServices) -> None:
        with pytest.raises(FeatureRequestNotFound):
            cast_vote(services, feature_request_id=uuid4(), user_id=uuid4())

    def test_idempotency_key_returns_cached_result(self, services: FeatureRequestServices) -> None:
        author = uuid4()
        fr = _seed(services, author)
        voter = uuid4()
        first = cast_vote(
            services,
            feature_request_id=fr.id,
            user_id=voter,
            idempotency_key="abc",
        )
        # Mutate the store to prove the cached result is returned without touching the repo.
        services.votes.counts[fr.id] = 999  # type: ignore[attr-defined]
        second = cast_vote(
            services,
            feature_request_id=fr.id,
            user_id=voter,
            idempotency_key="abc",
        )
        assert second == first


@pytest.mark.unit
class TestRetract:
    def test_retract_decrements_when_present(self, services: FeatureRequestServices) -> None:
        author = uuid4()
        fr = _seed(services, author)
        services.votes.counts[fr.id] = 1  # type: ignore[attr-defined]
        services.votes.voters[fr.id] = {author}  # type: ignore[attr-defined]
        result = retract_vote(services, feature_request_id=fr.id, user_id=author)
        assert result.voted is False
        assert result.vote_count == 0

    def test_retract_is_idempotent_when_absent(self, services: FeatureRequestServices) -> None:
        author = uuid4()
        fr = _seed(services, author)
        services.votes.counts[fr.id] = 1  # type: ignore[attr-defined]
        services.votes.voters[fr.id] = {author}  # type: ignore[attr-defined]
        stranger = uuid4()
        first = retract_vote(services, feature_request_id=fr.id, user_id=stranger)
        second = retract_vote(services, feature_request_id=fr.id, user_id=stranger)
        assert first.vote_count == 1
        assert second.vote_count == 1
