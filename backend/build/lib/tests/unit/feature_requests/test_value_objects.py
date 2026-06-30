"""Domain value-object invariants."""
import pytest

from apps.feature_requests.domain import (
    ACTIVE_STATUSES,
    Description,
    FeatureRequestStatus,
    InvalidDescription,
    InvalidTitle,
    SortOption,
    Title,
)


@pytest.mark.unit
class TestTitle:
    def test_strips_whitespace(self) -> None:
        assert Title("  Hello world  ").value == "Hello world"

    @pytest.mark.parametrize("bad", ["", "   ", "x" * 201])
    def test_rejects_invalid_lengths(self, bad: str) -> None:
        with pytest.raises(InvalidTitle):
            Title(bad)


@pytest.mark.unit
class TestDescription:
    def test_allows_empty(self) -> None:
        assert Description("").value == ""

    def test_rejects_over_5000_chars(self) -> None:
        with pytest.raises(InvalidDescription):
            Description("x" * 5001)


@pytest.mark.unit
def test_active_statuses_match_spec() -> None:
    # ADR-01: only these statuses participate in the default `top` ranking.
    assert ACTIVE_STATUSES == {
        FeatureRequestStatus.OPEN,
        FeatureRequestStatus.UNDER_REVIEW,
        FeatureRequestStatus.PLANNED,
        FeatureRequestStatus.IN_PROGRESS,
    }


@pytest.mark.unit
def test_sort_options() -> None:
    assert {SortOption(v).value for v in ("top", "hot", "new")} == {"top", "hot", "new"}
