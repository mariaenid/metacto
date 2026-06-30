"""Pure domain entities for feature requests."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

from .value_objects import (
    ACTIVE_STATUSES,
    Description,
    FeatureRequestStatus,
    Title,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class FeatureRequest:
    id: UUID
    title: Title
    description: Description
    author_id: UUID
    status: FeatureRequestStatus = FeatureRequestStatus.OPEN
    vote_count: int = 1  # author implicit vote at submission (RULE-04)
    duplicate_of_id: UUID | None = None
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    @classmethod
    def submit(cls, *, title: Title, description: Description, author_id: UUID) -> "FeatureRequest":
        return cls(id=uuid4(), title=title, description=description, author_id=author_id)

    def is_active(self) -> bool:
        # Drives the default `top` filter (see ADR-01).
        return self.status in ACTIVE_STATUSES
