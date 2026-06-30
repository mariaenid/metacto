"""Ports for the comments application layer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from ..domain import Body, Comment


@dataclass(frozen=True, slots=True)
class CommentPage:
    items: list[Comment]
    total: int


class CommentRepository(Protocol):
    def create(self, comment: Comment) -> None: ...
    def get_by_id(self, comment_id: UUID) -> Comment | None: ...
    def list_for_request(
        self, *, feature_request_id: UUID, limit: int, offset: int
    ) -> CommentPage: ...
    def edit(self, *, comment_id: UUID, body: Body, updated_at) -> Comment: ...
    def soft_delete(self, *, comment_id: UUID) -> Comment: ...
    def moderator_hide(self, *, comment_id: UUID) -> Comment: ...


@dataclass(frozen=True, slots=True)
class CommentServices:
    comments: CommentRepository
