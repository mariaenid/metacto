"""Comment use cases."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from ..domain import (
    Body,
    Comment,
    CommentNotEditable,
    CommentNotFound,
    NotCommentAuthor,
)
from .ports import CommentPage, CommentServices


def post_comment(
    services: CommentServices,
    *,
    feature_request_id: UUID,
    author_id: UUID,
    body: str,
) -> Comment:
    comment = Comment.post(
        feature_request_id=feature_request_id,
        author_id=author_id,
        body=Body(body),
    )
    services.comments.create(comment)
    return comment


def list_comments(
    services: CommentServices,
    *,
    feature_request_id: UUID,
    limit: int,
    offset: int,
) -> CommentPage:
    return services.comments.list_for_request(
        feature_request_id=feature_request_id,
        limit=limit,
        offset=offset,
    )


def edit_comment(
    services: CommentServices,
    *,
    comment_id: UUID,
    editor_id: UUID,
    body: str,
) -> Comment:
    comment = services.comments.get_by_id(comment_id)
    if comment is None:
        raise CommentNotFound(str(comment_id))
    if comment.author_id != editor_id:
        raise NotCommentAuthor("Only the author may edit a comment.")
    if comment.is_deleted or comment.is_hidden:
        raise CommentNotEditable("Cannot edit a deleted or hidden comment.")
    return services.comments.edit(
        comment_id=comment_id,
        body=Body(body),
        updated_at=datetime.now(UTC),
    )


def delete_comment(
    services: CommentServices,
    *,
    comment_id: UUID,
    requester_id: UUID,
    is_moderator: bool = False,
) -> Comment:
    comment = services.comments.get_by_id(comment_id)
    if comment is None:
        raise CommentNotFound(str(comment_id))
    if not is_moderator and comment.author_id != requester_id:
        raise NotCommentAuthor("Only the author or a moderator may delete a comment.")
    return services.comments.soft_delete(comment_id=comment_id)


def moderator_hide_comment(
    services: CommentServices,
    *,
    comment_id: UUID,
) -> Comment:
    comment = services.comments.get_by_id(comment_id)
    if comment is None:
        raise CommentNotFound(str(comment_id))
    return services.comments.moderator_hide(comment_id=comment_id)
