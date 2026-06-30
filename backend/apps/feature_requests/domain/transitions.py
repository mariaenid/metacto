"""Status state machine (ADR-02). Pure function; no DB."""

from __future__ import annotations

from .value_objects import FeatureRequestStatus as S

_FORWARD: dict[S, frozenset[S]] = {
    S.OPEN: frozenset({S.UNDER_REVIEW, S.CLOSED, S.DUPLICATE}),
    S.UNDER_REVIEW: frozenset({S.PLANNED, S.CLOSED, S.DUPLICATE}),
    S.PLANNED: frozenset({S.IN_PROGRESS, S.CLOSED, S.DUPLICATE}),
    S.IN_PROGRESS: frozenset({S.SHIPPED, S.CLOSED, S.DUPLICATE}),
    S.SHIPPED: frozenset(),  # terminal
    S.CLOSED: frozenset(),  # terminal
    S.DUPLICATE: frozenset(),  # terminal
}


def is_valid_transition(*, from_status: S, to_status: S) -> bool:
    return to_status in _FORWARD.get(from_status, frozenset())


class InvalidTransition(ValueError):
    def __init__(self, *, from_status: S, to_status: S) -> None:
        super().__init__(f"{from_status.value} -> {to_status.value} is not allowed")
        self.from_status = from_status
        self.to_status = to_status


class DuplicateRequiresTarget(ValueError):
    pass


class DuplicateCycle(ValueError):
    pass


class StatusConflict(RuntimeError):
    """Optimistic lock failure: the row is no longer in the expected status."""
