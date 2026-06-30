"""Vote entity. The Vote row itself is the source of truth for whether a user
has voted; FeatureRequest.vote_count is a denormalised cache kept atomic with it."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


def _now() -> datetime:
    return datetime.now(UTC)


@dataclass(slots=True)
class Vote:
    id: UUID
    feature_request_id: UUID
    user_id: UUID
    created_at: datetime = field(default_factory=_now)

    @classmethod
    def cast(cls, *, feature_request_id: UUID, user_id: UUID) -> Vote:
        return cls(
            id=uuid4(),
            feature_request_id=feature_request_id,
            user_id=user_id,
        )
