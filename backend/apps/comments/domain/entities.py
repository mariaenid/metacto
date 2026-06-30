"""Pure comment domain entities."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from .value_objects import Body


def _now() -> datetime:
    return datetime.now(UTC)


@dataclass(slots=True)
class Comment:
    id: UUID
    feature_request_id: UUID
    author_id: UUID
    body: Body
    is_deleted: bool = False  # author or moderator soft-delete
    is_hidden: bool = False  # moderator suppression (body still stored)
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    @classmethod
    def post(cls, *, feature_request_id: UUID, author_id: UUID, body: Body) -> Comment:
        return cls(
            id=uuid4(), feature_request_id=feature_request_id, author_id=author_id, body=body
        )

    def display_body(self) -> str:
        # Callers render this; the domain keeps the tombstone logic here.
        if self.is_deleted:
            return "[deleted]"
        if self.is_hidden:
            return "[hidden by a moderator]"
        return self.body.value
