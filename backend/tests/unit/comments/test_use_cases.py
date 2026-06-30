"""Unit tests for comment use cases — in-memory stub, no DB."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from apps.comments.application import (
    CommentPage,
    CommentServices,
    delete_comment,
    edit_comment,
    moderator_hide_comment,
    post_comment,
)
from apps.comments.domain import (
    Body,
    Comment,
    CommentNotEditable,
    CommentNotFound,
    InvalidBody,
    NotCommentAuthor,
)

# ---------------------------------------------------------------------------
# In-memory stub
# ---------------------------------------------------------------------------


@dataclass
class _StubRepo:
    store: dict[UUID, Comment] = field(default_factory=dict)

    def create(self, comment: Comment) -> None:
        self.store[comment.id] = comment

    def get_by_id(self, comment_id: UUID) -> Comment | None:
        return self.store.get(comment_id)

    def list_for_request(self, *, feature_request_id, limit, offset) -> CommentPage:
        items = [c for c in self.store.values() if c.feature_request_id == feature_request_id]
        return CommentPage(items=items[offset : offset + limit], total=len(items))

    def edit(self, *, comment_id, body, updated_at) -> Comment:
        c = self.store[comment_id]
        updated = Comment(
            id=c.id,
            feature_request_id=c.feature_request_id,
            author_id=c.author_id,
            body=body,
            is_deleted=c.is_deleted,
            is_hidden=c.is_hidden,
            created_at=c.created_at,
            updated_at=updated_at,
        )
        self.store[comment_id] = updated
        return updated

    def soft_delete(self, *, comment_id) -> Comment:
        c = self.store[comment_id]
        updated = Comment(
            id=c.id,
            feature_request_id=c.feature_request_id,
            author_id=c.author_id,
            body=c.body,
            is_deleted=True,
            is_hidden=c.is_hidden,
            created_at=c.created_at,
            updated_at=datetime.now(UTC),
        )
        self.store[comment_id] = updated
        return updated

    def moderator_hide(self, *, comment_id) -> Comment:
        c = self.store[comment_id]
        updated = Comment(
            id=c.id,
            feature_request_id=c.feature_request_id,
            author_id=c.author_id,
            body=c.body,
            is_deleted=c.is_deleted,
            is_hidden=True,
            created_at=c.created_at,
            updated_at=datetime.now(UTC),
        )
        self.store[comment_id] = updated
        return updated


def _services() -> CommentServices:
    return CommentServices(comments=_StubRepo())


# ---------------------------------------------------------------------------
# Value object
# ---------------------------------------------------------------------------


class TestBody:
    def test_empty_raises(self) -> None:
        with pytest.raises(InvalidBody):
            Body("   ")

    def test_too_long_raises(self) -> None:
        with pytest.raises(InvalidBody):
            Body("x" * 5001)

    def test_strips_whitespace(self) -> None:
        assert Body("  hello  ").value == "hello"


# ---------------------------------------------------------------------------
# Use cases
# ---------------------------------------------------------------------------


class TestPostComment:
    def test_creates_comment(self) -> None:
        svc = _services()
        fr_id, author_id = uuid4(), uuid4()
        comment = post_comment(svc, feature_request_id=fr_id, author_id=author_id, body="nice idea")
        assert comment.feature_request_id == fr_id
        assert comment.author_id == author_id
        assert comment.body.value == "nice idea"
        assert not comment.is_deleted

    def test_invalid_body_raises(self) -> None:
        with pytest.raises(InvalidBody):
            post_comment(_services(), feature_request_id=uuid4(), author_id=uuid4(), body="  ")


class TestEditComment:
    def test_author_can_edit(self) -> None:
        svc = _services()
        fr_id, author_id = uuid4(), uuid4()
        c = post_comment(svc, feature_request_id=fr_id, author_id=author_id, body="original")
        updated = edit_comment(svc, comment_id=c.id, editor_id=author_id, body="revised")
        assert updated.body.value == "revised"

    def test_non_author_cannot_edit(self) -> None:
        svc = _services()
        c = post_comment(svc, feature_request_id=uuid4(), author_id=uuid4(), body="x")
        with pytest.raises(NotCommentAuthor):
            edit_comment(svc, comment_id=c.id, editor_id=uuid4(), body="hijack")

    def test_deleted_comment_not_editable(self) -> None:
        svc = _services()
        author_id = uuid4()
        c = post_comment(svc, feature_request_id=uuid4(), author_id=author_id, body="bye")
        delete_comment(svc, comment_id=c.id, requester_id=author_id)
        with pytest.raises(CommentNotEditable):
            edit_comment(svc, comment_id=c.id, editor_id=author_id, body="edited after delete")

    def test_missing_raises_not_found(self) -> None:
        with pytest.raises(CommentNotFound):
            edit_comment(_services(), comment_id=uuid4(), editor_id=uuid4(), body="x")


class TestDeleteComment:
    def test_author_can_delete(self) -> None:
        svc = _services()
        author_id = uuid4()
        c = post_comment(svc, feature_request_id=uuid4(), author_id=author_id, body="bye")
        deleted = delete_comment(svc, comment_id=c.id, requester_id=author_id)
        assert deleted.is_deleted

    def test_moderator_can_delete_others(self) -> None:
        svc = _services()
        c = post_comment(svc, feature_request_id=uuid4(), author_id=uuid4(), body="bad")
        deleted = delete_comment(svc, comment_id=c.id, requester_id=uuid4(), is_moderator=True)
        assert deleted.is_deleted

    def test_non_author_non_moderator_cannot_delete(self) -> None:
        svc = _services()
        c = post_comment(svc, feature_request_id=uuid4(), author_id=uuid4(), body="ok")
        with pytest.raises(NotCommentAuthor):
            delete_comment(svc, comment_id=c.id, requester_id=uuid4(), is_moderator=False)


class TestModeratorHide:
    def test_hides_comment(self) -> None:
        svc = _services()
        c = post_comment(svc, feature_request_id=uuid4(), author_id=uuid4(), body="flagged")
        hidden = moderator_hide_comment(svc, comment_id=c.id)
        assert hidden.is_hidden

    def test_missing_raises_not_found(self) -> None:
        with pytest.raises(CommentNotFound):
            moderator_hide_comment(_services(), comment_id=uuid4())


class TestDisplayBody:
    def test_deleted_shows_tombstone(self) -> None:
        svc = _services()
        author_id = uuid4()
        c = post_comment(svc, feature_request_id=uuid4(), author_id=author_id, body="secret")
        deleted = delete_comment(svc, comment_id=c.id, requester_id=author_id)
        assert deleted.display_body() == "[deleted]"

    def test_hidden_shows_moderator_message(self) -> None:
        svc = _services()
        c = post_comment(svc, feature_request_id=uuid4(), author_id=uuid4(), body="offensive")
        hidden = moderator_hide_comment(svc, comment_id=c.id)
        assert hidden.display_body() == "[hidden by a moderator]"

    def test_visible_shows_body(self) -> None:
        svc = _services()
        c = post_comment(svc, feature_request_id=uuid4(), author_id=uuid4(), body="great idea")
        assert c.display_body() == "great idea"
