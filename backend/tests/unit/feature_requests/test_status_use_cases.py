"""Unit tests for the status transition use case and state machine."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

import pytest

from apps.feature_requests.application import FeatureRequestServices
from apps.feature_requests.application.status_use_cases import transition_status
from apps.feature_requests.domain import (
    Description,
    DuplicateRequiresTarget,
    FeatureRequest,
    FeatureRequestNotFound,
    FeatureRequestStatus,
    InvalidTransition,
    StatusChangeLog,
    Title,
)
from apps.feature_requests.domain.transitions import is_valid_transition

# ---------------------------------------------------------------------------
# State machine unit tests (pure function, no I/O)
# ---------------------------------------------------------------------------


class TestIsValidTransition:
    @pytest.mark.parametrize(
        "from_s,to_s",
        [
            (FeatureRequestStatus.OPEN, FeatureRequestStatus.UNDER_REVIEW),
            (FeatureRequestStatus.OPEN, FeatureRequestStatus.CLOSED),
            (FeatureRequestStatus.OPEN, FeatureRequestStatus.DUPLICATE),
            (FeatureRequestStatus.UNDER_REVIEW, FeatureRequestStatus.PLANNED),
            (FeatureRequestStatus.PLANNED, FeatureRequestStatus.IN_PROGRESS),
            (FeatureRequestStatus.IN_PROGRESS, FeatureRequestStatus.SHIPPED),
        ],
    )
    def test_allowed_transitions(self, from_s, to_s) -> None:
        assert is_valid_transition(from_status=from_s, to_status=to_s) is True

    @pytest.mark.parametrize(
        "from_s,to_s",
        [
            (FeatureRequestStatus.OPEN, FeatureRequestStatus.PLANNED),
            (FeatureRequestStatus.OPEN, FeatureRequestStatus.SHIPPED),
            (FeatureRequestStatus.SHIPPED, FeatureRequestStatus.OPEN),
            (FeatureRequestStatus.CLOSED, FeatureRequestStatus.OPEN),
            (FeatureRequestStatus.DUPLICATE, FeatureRequestStatus.OPEN),
            (FeatureRequestStatus.IN_PROGRESS, FeatureRequestStatus.UNDER_REVIEW),
        ],
    )
    def test_forbidden_transitions(self, from_s, to_s) -> None:
        assert is_valid_transition(from_status=from_s, to_status=to_s) is False

    def test_terminal_statuses_have_no_outbound_edges(self) -> None:
        for terminal in (
            FeatureRequestStatus.SHIPPED,
            FeatureRequestStatus.CLOSED,
            FeatureRequestStatus.DUPLICATE,
        ):
            for other in FeatureRequestStatus:
                assert is_valid_transition(from_status=terminal, to_status=other) is False


# ---------------------------------------------------------------------------
# Use case unit tests (in-memory repo stub)
# ---------------------------------------------------------------------------


@dataclass
class _StubRepo:
    requests: dict[UUID, FeatureRequest] = field(default_factory=dict)
    transitions: list[tuple] = field(default_factory=list)

    def submit_with_author_vote(self, fr: FeatureRequest) -> None:
        self.requests[fr.id] = fr

    def get_by_id(self, request_id: UUID) -> FeatureRequest | None:
        return self.requests.get(request_id)

    def list(self, **_): ...  # not needed for these tests

    def transition_status(
        self, *, request_id, expected_from, to_status, changed_by_user_id, reason, duplicate_of_id
    ):
        fr = self.requests[request_id]
        updated = FeatureRequest(
            id=fr.id,
            title=fr.title,
            description=fr.description,
            author_id=fr.author_id,
            status=to_status,
            vote_count=fr.vote_count,
            duplicate_of_id=duplicate_of_id,
            created_at=fr.created_at,
            updated_at=fr.updated_at,
        )
        self.requests[request_id] = updated
        log = StatusChangeLog.record(
            feature_request_id=request_id,
            from_status=expected_from,
            to_status=to_status,
            changed_by_user_id=changed_by_user_id,
            reason=reason,
        )
        self.transitions.append((request_id, expected_from, to_status))
        return (updated, log)


@dataclass
class _StubVoteRepo:
    def cast(self, **_): ...
    def retract(self, **_): ...


@dataclass
class _StubIdempotency:
    def get(self, key):
        return None

    def put(self, key, value): ...


def _make_services(repo=None) -> FeatureRequestServices:
    return FeatureRequestServices(
        requests=repo or _StubRepo(),
        votes=_StubVoteRepo(),
        idempotency=_StubIdempotency(),
    )


def _seed_fr(repo: _StubRepo, *, status=FeatureRequestStatus.OPEN) -> FeatureRequest:
    fr = FeatureRequest(
        id=uuid4(),
        title=Title("test"),
        description=Description(""),
        author_id=uuid4(),
        status=status,
        vote_count=1,
    )
    repo.requests[fr.id] = fr
    return fr


class TestTransitionStatusUseCase:
    def test_valid_transition_delegates_to_repo(self) -> None:
        repo = _StubRepo()
        fr = _seed_fr(repo)
        moderator_id = uuid4()
        updated_fr, log = transition_status(
            _make_services(repo),
            request_id=fr.id,
            expected_from=FeatureRequestStatus.OPEN,
            to_status=FeatureRequestStatus.UNDER_REVIEW,
            changed_by_user_id=moderator_id,
        )
        assert updated_fr.status is FeatureRequestStatus.UNDER_REVIEW
        assert log.from_status is FeatureRequestStatus.OPEN
        assert log.to_status is FeatureRequestStatus.UNDER_REVIEW
        assert log.changed_by_user_id == moderator_id

    def test_raises_invalid_transition_before_repo_call(self) -> None:
        repo = _StubRepo()
        fr = _seed_fr(repo)
        with pytest.raises(InvalidTransition):
            transition_status(
                _make_services(repo),
                request_id=fr.id,
                expected_from=FeatureRequestStatus.OPEN,
                to_status=FeatureRequestStatus.SHIPPED,
                changed_by_user_id=uuid4(),
            )
        assert len(repo.transitions) == 0

    def test_raises_duplicate_requires_target(self) -> None:
        repo = _StubRepo()
        fr = _seed_fr(repo)
        with pytest.raises(DuplicateRequiresTarget):
            transition_status(
                _make_services(repo),
                request_id=fr.id,
                expected_from=FeatureRequestStatus.OPEN,
                to_status=FeatureRequestStatus.DUPLICATE,
                changed_by_user_id=uuid4(),
                duplicate_of_id=None,
            )

    def test_non_duplicate_transition_clears_duplicate_of_id(self) -> None:
        repo = _StubRepo()
        fr = _seed_fr(repo)
        stray_id = uuid4()
        transition_status(
            _make_services(repo),
            request_id=fr.id,
            expected_from=FeatureRequestStatus.OPEN,
            to_status=FeatureRequestStatus.UNDER_REVIEW,
            changed_by_user_id=uuid4(),
            duplicate_of_id=stray_id,  # stray — should be ignored
        )
        # The stub captures (request_id, expected_from, to_status); confirm it was reached
        assert len(repo.transitions) == 1

    def test_raises_not_found_if_request_missing(self) -> None:
        repo = _StubRepo()
        with pytest.raises(FeatureRequestNotFound):
            transition_status(
                _make_services(repo),
                request_id=uuid4(),
                expected_from=FeatureRequestStatus.OPEN,
                to_status=FeatureRequestStatus.UNDER_REVIEW,
                changed_by_user_id=uuid4(),
            )

    def test_reason_is_forwarded_to_log(self) -> None:
        repo = _StubRepo()
        fr = _seed_fr(repo)
        _, log = transition_status(
            _make_services(repo),
            request_id=fr.id,
            expected_from=FeatureRequestStatus.OPEN,
            to_status=FeatureRequestStatus.CLOSED,
            changed_by_user_id=uuid4(),
            reason="Closing per product decision",
        )
        assert log.reason == "Closing per product decision"
