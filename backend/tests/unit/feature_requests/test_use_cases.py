"""Feature request use cases with an in-memory repository."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from uuid import UUID, uuid4

import pytest

from apps.feature_requests.application import (
    FeatureRequestServices,
    ListPage,
    get_feature_request,
    list_feature_requests,
    submit_feature_request,
)
from apps.feature_requests.domain import (
    FeatureRequest,
    FeatureRequestNotFound,
    FeatureRequestStatus,
    InvalidTitle,
    SortOption,
)


@dataclass(slots=True)
class _Repo:
    by_id: dict[UUID, FeatureRequest] = field(default_factory=dict)
    author_votes: dict[UUID, UUID] = field(default_factory=dict)

    def submit_with_author_vote(self, fr: FeatureRequest) -> None:
        self.by_id[fr.id] = fr
        self.author_votes[fr.id] = fr.author_id

    def get_by_id(self, request_id: UUID) -> FeatureRequest | None:
        return self.by_id.get(request_id)

    def list(self, *, sort: SortOption, limit: int, offset: int) -> ListPage:
        items = list(self.by_id.values())
        if sort is SortOption.TOP:
            items = [i for i in items if i.is_active()]
            items.sort(key=lambda i: (-i.vote_count, -i.created_at.timestamp()))
        elif sort is SortOption.NEW:
            items.sort(key=lambda i: -i.created_at.timestamp())
        elif sort is SortOption.HOT:
            items.sort(key=lambda i: -i.vote_count)
        page = items[offset : offset + limit]
        digest = hashlib.sha256(
            b"|".join(f"{i.id}:{i.vote_count}".encode() for i in page)
        ).hexdigest()
        return ListPage(items=page, total=len(items), fingerprint=digest)


@dataclass
class _NullVoteRepo:
    def cast(self, **_): ...
    def retract(self, **_): ...


@dataclass
class _NullIdempotency:
    def get(self, key):
        return None

    def put(self, key, value): ...


@pytest.fixture
def services() -> FeatureRequestServices:
    return FeatureRequestServices(
        requests=_Repo(), votes=_NullVoteRepo(), idempotency=_NullIdempotency()
    )


@pytest.mark.unit
class TestSubmit:
    def test_creates_request_with_author_vote(self, services: FeatureRequestServices) -> None:
        author = uuid4()
        fr = submit_feature_request(
            services, title="Dark mode", description="Please", author_id=author
        )
        assert fr.author_id == author
        assert fr.vote_count == 1
        assert services.requests.author_votes[fr.id] == author  # type: ignore[attr-defined]

    def test_invalid_title_raises(self, services: FeatureRequestServices) -> None:
        with pytest.raises(InvalidTitle):
            submit_feature_request(services, title="", description="", author_id=uuid4())


@pytest.mark.unit
class TestGet:
    def test_missing_raises(self, services: FeatureRequestServices) -> None:
        with pytest.raises(FeatureRequestNotFound):
            get_feature_request(services, request_id=uuid4())


@pytest.mark.unit
class TestList:
    def test_top_excludes_inactive(self, services: FeatureRequestServices) -> None:
        author = uuid4()
        fr_open = submit_feature_request(services, title="active", description="", author_id=author)
        fr_shipped = submit_feature_request(
            services, title="done", description="", author_id=author
        )
        services.requests.by_id[fr_shipped.id].status = FeatureRequestStatus.SHIPPED  # type: ignore[attr-defined]
        page = list_feature_requests(services, sort=SortOption.TOP, limit=10, offset=0)
        ids = [r.id for r in page.items]
        assert fr_open.id in ids
        assert fr_shipped.id not in ids

    def test_new_includes_all_statuses(self, services: FeatureRequestServices) -> None:
        author = uuid4()
        a = submit_feature_request(services, title="a", description="", author_id=author)
        b = submit_feature_request(services, title="b", description="", author_id=author)
        services.requests.by_id[a.id].status = FeatureRequestStatus.SHIPPED  # type: ignore[attr-defined]
        page = list_feature_requests(services, sort=SortOption.NEW, limit=10, offset=0)
        assert {r.id for r in page.items} == {a.id, b.id}
