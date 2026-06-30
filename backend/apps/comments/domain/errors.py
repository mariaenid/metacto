"""Domain errors for the comments context."""

from __future__ import annotations


class CommentError(Exception):
    pass


class CommentNotFound(CommentError):
    pass


class CommentNotEditable(CommentError):
    """Author attempted to edit a deleted or hidden comment."""


class NotCommentAuthor(CommentError):
    """Requester is not the comment's author."""
