"""FeatureRequest entity behaviour."""
from uuid import uuid4

import pytest

from apps.feature_requests.domain import (
    Description,
    FeatureRequest,
    FeatureRequestStatus,
    Title,
)


@pytest.mark.unit
class TestFeatureRequest:
    def test_submit_initialises_with_author_implicit_vote(self) -> None:
        fr = FeatureRequest.submit(
            title=Title("Add dark mode"),
            description=Description(""),
            author_id=uuid4(),
        )
        # RULE-04: author's vote is recorded; the count reflects it from the start.
        assert fr.vote_count == 1
        assert fr.status is FeatureRequestStatus.OPEN
        assert fr.duplicate_of_id is None

    def test_is_active_matches_status(self) -> None:
        fr = FeatureRequest.submit(
            title=Title("x"), description=Description(""), author_id=uuid4()
        )
        assert fr.is_active() is True
        fr.status = FeatureRequestStatus.SHIPPED
        assert fr.is_active() is False
        fr.status = FeatureRequestStatus.IN_PROGRESS
        assert fr.is_active() is True
