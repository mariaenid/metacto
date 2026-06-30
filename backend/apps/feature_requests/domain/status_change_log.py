"""StatusChangeLog entity. Written transactionally with each status update (RULE-08)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from .value_objects import FeatureRequestStatus


def _now() -> datetime:
    return datetime.now(UTC)


@dataclass(slots=True)
class StatusChangeLog:
    id: UUID
    feature_request_id: UUID
    from_status: FeatureRequestStatus
    to_status: FeatureRequestStatus
    changed_by_user_id: UUID
    reason: str | None = None
    changed_at: datetime = field(default_factory=_now)

    @classmethod
    def record(
        cls,
        *,
        feature_request_id: UUID,
        from_status: FeatureRequestStatus,
        to_status: FeatureRequestStatus,
        changed_by_user_id: UUID,
        reason: str | None = None,
    ) -> StatusChangeLog:
        return cls(
            id=uuid4(),
            feature_request_id=feature_request_id,
            from_status=from_status,
            to_status=to_status,
            changed_by_user_id=changed_by_user_id,
            reason=reason,
        )
