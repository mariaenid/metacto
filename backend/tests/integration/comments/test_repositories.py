"""Integration tests for DjangoCommentRepository against real database."""

from __future__ import annotations

from datetime import UTC

import pytest

from apps.comments.domain import Body, Comment
from apps.comments.infrastructure.models import CommentRecord
from apps.comments.infrastructure.repositories import DjangoCommentRepository
from apps.feature_requests.domain import Description, FeatureRequest, Title
from apps.feature_requests.infrastructure.repositories import DjangoFeatureRequestRepository
from apps.identity.domain import Email, User
from apps.identity.infrastructure.repositories import DjangoUserRepository


@pytest.fixture
def author():
    users = DjangoUserRepository()
    user = User.register(email=Email("cmt-author@example.com"), display_name="A", password_hash="h")
    users.add(user)
    return user


@pytest.fixture
def feature_request(author) -> FeatureRequest:
    fr = FeatureRequest.submit(
        title=Title("fr for comments"), description=Description(""), author_id=author.id
    )
    DjangoFeatureRequestRepository().submit_with_author_vote(fr)
    return fr


@pytest.fixture
def repo() -> DjangoCommentRepository:
    return DjangoCommentRepository()


def _post(repo, *, fr_id, author_id, body="hello") -> Comment:
    c = Comment.post(feature_request_id=fr_id, author_id=author_id, body=Body(body))
    repo.create(c)
    return c


@pytest.mark.integration
@pytest.mark.django_db
class TestCreate:
    def test_persists_comment(self, author, feature_request, repo) -> None:
        c = _post(repo, fr_id=feature_request.id, author_id=author.id)
        assert CommentRecord.objects.filter(id=c.id).exists()

    def test_list_returns_in_chronological_order(self, author, feature_request, repo) -> None:
        c1 = _post(repo, fr_id=feature_request.id, author_id=author.id, body="first")
        c2 = _post(repo, fr_id=feature_request.id, author_id=author.id, body="second")
        page = repo.list_for_request(feature_request_id=feature_request.id, limit=10, offset=0)
        assert page.items[0].id == c1.id
        assert page.items[1].id == c2.id
        assert page.total == 2


@pytest.mark.integration
@pytest.mark.django_db
class TestEdit:
    def test_updates_body_in_db(self, author, feature_request, repo) -> None:
        from datetime import datetime

        c = _post(repo, fr_id=feature_request.id, author_id=author.id)
        updated = repo.edit(
            comment_id=c.id,
            body=Body("edited body"),
            updated_at=datetime.now(UTC),
        )
        assert updated.body.value == "edited body"
        assert CommentRecord.objects.get(id=c.id).body == "edited body"


@pytest.mark.integration
@pytest.mark.django_db
class TestSoftDelete:
    def test_sets_is_deleted_flag(self, author, feature_request, repo) -> None:
        c = _post(repo, fr_id=feature_request.id, author_id=author.id)
        deleted = repo.soft_delete(comment_id=c.id)
        assert deleted.is_deleted
        assert CommentRecord.objects.get(id=c.id).is_deleted is True

    def test_row_still_exists_after_delete(self, author, feature_request, repo) -> None:
        c = _post(repo, fr_id=feature_request.id, author_id=author.id)
        repo.soft_delete(comment_id=c.id)
        assert CommentRecord.objects.filter(id=c.id).exists()


@pytest.mark.integration
@pytest.mark.django_db
class TestModeratorHide:
    def test_sets_is_hidden_flag(self, author, feature_request, repo) -> None:
        c = _post(repo, fr_id=feature_request.id, author_id=author.id)
        hidden = repo.moderator_hide(comment_id=c.id)
        assert hidden.is_hidden
        assert CommentRecord.objects.get(id=c.id).is_hidden is True
