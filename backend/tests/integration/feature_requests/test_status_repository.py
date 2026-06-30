"""Integration tests for status transition repository — optimistic locking and cycle detection."""

from __future__ import annotations

import pytest

from apps.feature_requests.domain import (
    Description,
    DuplicateCycle,
    FeatureRequest,
    FeatureRequestStatus,
    StatusConflict,
    Title,
)
from apps.feature_requests.infrastructure.models import (
    FeatureRequestRecord,
    StatusChangeLogRecord,
)
from apps.feature_requests.infrastructure.repositories import DjangoFeatureRequestRepository
from apps.identity.domain import Email, User
from apps.identity.infrastructure.repositories import DjangoUserRepository


@pytest.fixture
def moderator():
    users = DjangoUserRepository()
    user = User.register(email=Email("mod@example.com"), display_name="Mod", password_hash="h")
    users.add(user)
    return user


@pytest.fixture
def author():
    users = DjangoUserRepository()
    user = User.register(
        email=Email("author2@example.com"), display_name="Author", password_hash="h"
    )
    users.add(user)
    return user


@pytest.fixture
def repo() -> DjangoFeatureRequestRepository:
    return DjangoFeatureRequestRepository()


def _submit(repo: DjangoFeatureRequestRepository, *, author_id, title: str) -> FeatureRequest:
    fr = FeatureRequest.submit(title=Title(title), description=Description(""), author_id=author_id)
    repo.submit_with_author_vote(fr)
    return fr


@pytest.mark.integration
@pytest.mark.django_db
class TestTransitionStatus:
    def test_happy_path_updates_status_and_creates_log(self, author, moderator, repo) -> None:
        fr = _submit(repo, author_id=author.id, title="feature A")
        updated_fr, log = repo.transition_status(
            request_id=fr.id,
            expected_from=FeatureRequestStatus.OPEN,
            to_status=FeatureRequestStatus.UNDER_REVIEW,
            changed_by_user_id=moderator.id,
            reason="Triaging now",
            duplicate_of_id=None,
        )
        assert updated_fr.status is FeatureRequestStatus.UNDER_REVIEW
        assert log.from_status is FeatureRequestStatus.OPEN
        assert log.to_status is FeatureRequestStatus.UNDER_REVIEW
        assert log.reason == "Triaging now"

        db_row = FeatureRequestRecord.objects.get(id=fr.id)
        assert db_row.status == FeatureRequestStatus.UNDER_REVIEW.value

        assert StatusChangeLogRecord.objects.filter(feature_request_id=fr.id).count() == 1

    def test_status_conflict_raised_when_expected_from_is_stale(
        self, author, moderator, repo
    ) -> None:
        fr = _submit(repo, author_id=author.id, title="stale test")
        # Simulate concurrent transition already happened
        FeatureRequestRecord.objects.filter(id=fr.id).update(
            status=FeatureRequestStatus.UNDER_REVIEW.value
        )
        with pytest.raises(StatusConflict):
            repo.transition_status(
                request_id=fr.id,
                expected_from=FeatureRequestStatus.OPEN,  # stale
                to_status=FeatureRequestStatus.UNDER_REVIEW,
                changed_by_user_id=moderator.id,
                reason=None,
                duplicate_of_id=None,
            )
        # No log row should have been created
        assert StatusChangeLogRecord.objects.filter(feature_request_id=fr.id).count() == 0

    def test_duplicate_transition_sets_duplicate_of_id(self, author, moderator, repo) -> None:
        fr_a = _submit(repo, author_id=author.id, title="original")
        fr_b = _submit(repo, author_id=author.id, title="duplicate")
        repo.transition_status(
            request_id=fr_b.id,
            expected_from=FeatureRequestStatus.OPEN,
            to_status=FeatureRequestStatus.DUPLICATE,
            changed_by_user_id=moderator.id,
            reason=None,
            duplicate_of_id=fr_a.id,
        )
        db_row = FeatureRequestRecord.objects.get(id=fr_b.id)
        assert db_row.status == FeatureRequestStatus.DUPLICATE.value
        assert db_row.duplicate_of_id == fr_a.id

    def test_duplicate_cycle_direct_detected(self, author, moderator, repo) -> None:
        fr_a = _submit(repo, author_id=author.id, title="A")
        fr_b = _submit(repo, author_id=author.id, title="B")
        # Mark B as duplicate of A
        repo.transition_status(
            request_id=fr_b.id,
            expected_from=FeatureRequestStatus.OPEN,
            to_status=FeatureRequestStatus.DUPLICATE,
            changed_by_user_id=moderator.id,
            reason=None,
            duplicate_of_id=fr_a.id,
        )
        # Now try to mark A as duplicate of B — this would create A→B→A cycle
        with pytest.raises(DuplicateCycle):
            repo.transition_status(
                request_id=fr_a.id,
                expected_from=FeatureRequestStatus.OPEN,
                to_status=FeatureRequestStatus.DUPLICATE,
                changed_by_user_id=moderator.id,
                reason=None,
                duplicate_of_id=fr_b.id,
            )

    def test_duplicate_cycle_indirect_detected(self, author, moderator, repo) -> None:
        fr_a = _submit(repo, author_id=author.id, title="chain A")
        fr_b = _submit(repo, author_id=author.id, title="chain B")
        fr_c = _submit(repo, author_id=author.id, title="chain C")
        # B → A, C → B  (chain: C→B→A)
        repo.transition_status(
            request_id=fr_b.id,
            expected_from=FeatureRequestStatus.OPEN,
            to_status=FeatureRequestStatus.DUPLICATE,
            changed_by_user_id=moderator.id,
            reason=None,
            duplicate_of_id=fr_a.id,
        )
        repo.transition_status(
            request_id=fr_c.id,
            expected_from=FeatureRequestStatus.OPEN,
            to_status=FeatureRequestStatus.DUPLICATE,
            changed_by_user_id=moderator.id,
            reason=None,
            duplicate_of_id=fr_b.id,
        )
        # Marking A as duplicate of C would create A→C→B→A
        with pytest.raises(DuplicateCycle):
            repo.transition_status(
                request_id=fr_a.id,
                expected_from=FeatureRequestStatus.OPEN,
                to_status=FeatureRequestStatus.DUPLICATE,
                changed_by_user_id=moderator.id,
                reason=None,
                duplicate_of_id=fr_c.id,
            )

    def test_multiple_log_rows_accumulate_for_same_request(self, author, moderator, repo) -> None:
        fr = _submit(repo, author_id=author.id, title="multi-step")
        repo.transition_status(
            request_id=fr.id,
            expected_from=FeatureRequestStatus.OPEN,
            to_status=FeatureRequestStatus.UNDER_REVIEW,
            changed_by_user_id=moderator.id,
            reason=None,
            duplicate_of_id=None,
        )
        repo.transition_status(
            request_id=fr.id,
            expected_from=FeatureRequestStatus.UNDER_REVIEW,
            to_status=FeatureRequestStatus.PLANNED,
            changed_by_user_id=moderator.id,
            reason=None,
            duplicate_of_id=None,
        )
        assert StatusChangeLogRecord.objects.filter(feature_request_id=fr.id).count() == 2
