"""Value objects for the feature_requests context. No Django, no DRF."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

MIN_TITLE_LENGTH = 1
MAX_TITLE_LENGTH = 200
MAX_DESCRIPTION_LENGTH = 5000


class FeatureRequestStatus(StrEnum):
    OPEN = "open"
    UNDER_REVIEW = "under_review"
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    SHIPPED = "shipped"
    CLOSED = "closed"
    DUPLICATE = "duplicate"


ACTIVE_STATUSES: frozenset[FeatureRequestStatus] = frozenset(
    {
        FeatureRequestStatus.OPEN,
        FeatureRequestStatus.UNDER_REVIEW,
        FeatureRequestStatus.PLANNED,
        FeatureRequestStatus.IN_PROGRESS,
    }
)


class SortOption(StrEnum):
    TOP = "top"
    HOT = "hot"
    NEW = "new"


@dataclass(frozen=True, slots=True)
class Title:
    value: str

    def __post_init__(self) -> None:
        stripped = self.value.strip()
        if not (MIN_TITLE_LENGTH <= len(stripped) <= MAX_TITLE_LENGTH):
            raise InvalidTitle(f"title must be {MIN_TITLE_LENGTH}-{MAX_TITLE_LENGTH} characters")
        object.__setattr__(self, "value", stripped)


@dataclass(frozen=True, slots=True)
class Description:
    value: str

    def __post_init__(self) -> None:
        stripped = self.value.strip()
        if len(stripped) > MAX_DESCRIPTION_LENGTH:
            raise InvalidDescription(
                f"description must be at most {MAX_DESCRIPTION_LENGTH} characters"
            )
        object.__setattr__(self, "value", stripped)


class InvalidTitle(ValueError):
    pass


class InvalidDescription(ValueError):
    pass
