"""Status transition use case (ADR-02). Validates the state machine and delegates
the atomic UPDATE + log insert to the repository."""

from __future__ import annotations

from uuid import UUID

from ..domain import (
    DuplicateRequiresTarget,
    FeatureRequest,
    FeatureRequestNotFound,
    FeatureRequestStatus,
    InvalidTransition,
    StatusChangeLog,
    is_valid_transition,
)
from .use_cases import FeatureRequestServices


def transition_status(
    services: FeatureRequestServices,
    *,
    request_id: UUID,
    expected_from: FeatureRequestStatus,
    to_status: FeatureRequestStatus,
    changed_by_user_id: UUID,
    reason: str | None = None,
    duplicate_of_id: UUID | None = None,
) -> tuple[FeatureRequest, StatusChangeLog]:
    if not is_valid_transition(from_status=expected_from, to_status=to_status):
        raise InvalidTransition(from_status=expected_from, to_status=to_status)
    if to_status is FeatureRequestStatus.DUPLICATE and duplicate_of_id is None:
        raise DuplicateRequiresTarget("duplicate_of_id is required for status=duplicate")
    if to_status is not FeatureRequestStatus.DUPLICATE:
        duplicate_of_id = None  # ignore stray target on non-duplicate transitions

    if services.requests.get_by_id(request_id) is None:
        raise FeatureRequestNotFound(str(request_id))

    return services.requests.transition_status(
        request_id=request_id,
        expected_from=expected_from,
        to_status=to_status,
        changed_by_user_id=changed_by_user_id,
        reason=reason,
        duplicate_of_id=duplicate_of_id,
    )
