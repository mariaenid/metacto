"""Django ORM implementation of CommentRepository."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from django.db import transaction

from ..application.ports import CommentPage
from ..domain import Body, Comment
from .models import CommentRecord


def _from_record(row: CommentRecord) -> Comment:
    return Comment(
        id=row.id,
        feature_request_id=row.feature_request_id,
        author_id=row.author_id,
        body=Body.__new__(Body),  # skip validation — data is already stored clean
        is_deleted=row.is_deleted,
        is_hidden=row.is_hidden,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _from_record_with_body(row: CommentRecord) -> Comment:
    # Body was validated on write; bypass __post_init__ to avoid re-validating on read.
    c = Comment.__new__(Comment)
    c.id = row.id
    c.feature_request_id = row.feature_request_id
    c.author_id = row.author_id
    b = object.__new__(Body)
    object.__setattr__(b, "value", row.body)
    c.body = b
    c.is_deleted = row.is_deleted
    c.is_hidden = row.is_hidden
    c.created_at = row.created_at
    c.updated_at = row.updated_at
    return c


class DjangoCommentRepository:
    def create(self, comment: Comment) -> None:
        CommentRecord.objects.create(
            id=comment.id,
            feature_request_id=comment.feature_request_id,
            author_id=comment.author_id,
            body=comment.body.value,
            is_deleted=False,
            is_hidden=False,
            created_at=comment.created_at,
            updated_at=comment.updated_at,
        )

    def get_by_id(self, comment_id: UUID) -> Comment | None:
        row = CommentRecord.objects.filter(id=comment_id).first()
        return _from_record_with_body(row) if row else None

    def list_for_request(self, *, feature_request_id: UUID, limit: int, offset: int) -> CommentPage:
        qs = CommentRecord.objects.filter(feature_request_id=feature_request_id).order_by(
            "created_at"
        )
        total = qs.count()
        rows = list(qs[offset : offset + limit])
        return CommentPage(items=[_from_record_with_body(r) for r in rows], total=total)

    def edit(self, *, comment_id: UUID, body: Body, updated_at: datetime) -> Comment:
        with transaction.atomic():
            CommentRecord.objects.filter(id=comment_id).update(
                body=body.value, updated_at=updated_at
            )
            row = CommentRecord.objects.get(id=comment_id)
        return _from_record_with_body(row)

    def soft_delete(self, *, comment_id: UUID) -> Comment:
        with transaction.atomic():
            CommentRecord.objects.filter(id=comment_id).update(
                is_deleted=True, updated_at=datetime.now(UTC)
            )
            row = CommentRecord.objects.get(id=comment_id)
        return _from_record_with_body(row)

    def moderator_hide(self, *, comment_id: UUID) -> Comment:
        with transaction.atomic():
            CommentRecord.objects.filter(id=comment_id).update(
                is_hidden=True, updated_at=datetime.now(UTC)
            )
            row = CommentRecord.objects.get(id=comment_id)
        return _from_record_with_body(row)
