"""Ports for the feature_requests application layer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol
from uuid import UUID

from ..domain import (
    FeatureRequest,
    FeatureRequestStatus,
    SortOption,
    StatusChangeLog,
)


@dataclass(frozen=True, slots=True)
class ListPage:
    items: list[FeatureRequest]
    total: int
    fingerprint: str  # opaque hash for ETag; clients pass it back via If-None-Match


@dataclass(frozen=True, slots=True)
class VoteResult:
    feature_request_id: UUID
    voted: bool  # post-state: True if the user has a vote on this request now
    vote_count: int


class FeatureRequestRepository(Protocol):
    def submit_with_author_vote(self, request: FeatureRequest) -> None:
        """Insert the new request AND the author's implicit Vote row atomically (RULE-04)."""

    def get_by_id(self, request_id: UUID) -> FeatureRequest | None: ...

    def list(self, *, sort: SortOption, limit: int, offset: int) -> ListPage:
        """Paginated list. `top` filters to active statuses; `hot` and `new` see everything."""

    def transition_status(
        self,
        *,
        request_id: UUID,
        expected_from: FeatureRequestStatus,
        to_status: FeatureRequestStatus,
        changed_by_user_id: UUID,
        reason: str | None,
        duplicate_of_id: UUID | None,
    ) -> tuple[FeatureRequest, StatusChangeLog]:
        """Atomic optimistic-lock UPDATE on (id, status=expected_from). Raises
        StatusConflict on zero rows updated, DuplicateCycle if the proposed target
        forms a cycle, FeatureRequestNotFound if either id is missing."""


class VoteRepository(Protocol):
    def cast(self, *, feature_request_id: UUID, user_id: UUID) -> VoteResult:
        """Idempotent. Inserts a Vote row and atomically increments vote_count;
        returns the existing state if the user has already voted."""

    def retract(self, *, feature_request_id: UUID, user_id: UUID) -> VoteResult:
        """Idempotent. Deletes the Vote row and atomically decrements vote_count;
        returns the existing state if there is nothing to delete."""


class IdempotencyStore(Protocol):
    """Caches the result of a mutating request so retries with the same key return
    the original response (RULE-10). Keyed by (actor_id, route, idempotency_key)."""

    def get(self, key: str) -> Any | None: ...
    def put(self, key: str, value: Any) -> None: ...
