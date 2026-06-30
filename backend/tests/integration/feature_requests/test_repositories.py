"""Repository invariants against the real database."""

from __future__ import annotations

import pytest

from apps.feature_requests.application import ListPage
from apps.feature_requests.domain import (
    Description,
    FeatureRequest,
    FeatureRequestStatus,
    SortOption,
    Title,
)
from apps.feature_requests.infrastructure.models import FeatureRequestRecord, VoteRecord
from apps.feature_requests.infrastructure.repositories import (
    DjangoFeatureRequestRepository,
)
from apps.identity.domain import Email, User
from apps.identity.infrastructure.repositories import DjangoUserRepository


@pytest.fixture
def author():
    users = DjangoUserRepository()
    user = User.register(email=Email("author@example.com"), display_name="A", password_hash="h")
    users.add(user)
    return user


@pytest.fixture
def repo() -> DjangoFeatureRequestRepository:
    return DjangoFeatureRequestRepository()


def _submit(repo: DjangoFeatureRequestRepository, *, author_id, title: str) -> FeatureRequest:
    fr = FeatureRequest.submit(title=Title(title), description=Description(""), author_id=author_id)
    repo.submit_with_author_vote(fr)
    return fr


@pytest.mark.integration
@pytest.mark.django_db
class TestSubmit:
    def test_inserts_request_and_author_vote_atomically(self, author, repo) -> None:
        fr = _submit(repo, author_id=author.id, title="dark mode")
        assert FeatureRequestRecord.objects.filter(id=fr.id).exists()
        assert VoteRecord.objects.filter(feature_request_id=fr.id, user_id=author.id).exists()


@pytest.mark.integration
@pytest.mark.django_db
class TestList:
    def test_top_filters_inactive_statuses(self, author, repo) -> None:
        active = _submit(repo, author_id=author.id, title="active")
        shipped = _submit(repo, author_id=author.id, title="shipped")
        FeatureRequestRecord.objects.filter(id=shipped.id).update(
            status=FeatureRequestStatus.SHIPPED.value
        )
        page = repo.list(sort=SortOption.TOP, limit=10, offset=0)
        ids = {r.id for r in page.items}
        assert active.id in ids
        assert shipped.id not in ids

    def test_new_orders_by_creation_desc(self, author, repo) -> None:
        first = _submit(repo, author_id=author.id, title="one")
        second = _submit(repo, author_id=author.id, title="two")
        page = repo.list(sort=SortOption.NEW, limit=10, offset=0)
        assert page.items[0].id == second.id
        assert page.items[1].id == first.id

    def test_fingerprint_changes_when_vote_count_changes(self, author, repo) -> None:
        fr = _submit(repo, author_id=author.id, title="hello")
        first: ListPage = repo.list(sort=SortOption.NEW, limit=10, offset=0)
        FeatureRequestRecord.objects.filter(id=fr.id).update(vote_count=42)
        second: ListPage = repo.list(sort=SortOption.NEW, limit=10, offset=0)
        assert first.fingerprint != second.fingerprint
