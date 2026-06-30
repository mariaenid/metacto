"""Admin stats use case (Sprint 5). Read-only aggregate — no writes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class TopRequest:
    id: str
    title: str
    vote_count: int
    status: str


@dataclass(frozen=True, slots=True)
class AdminStats:
    counts_by_status: dict[str, int]
    activity_30d: dict[str, int]  # submissions, votes, transitions
    triage: dict[str, Any]  # oldest_open_at (ISO str | None), stale_under_review_count
    top_voted: list[TopRequest]


class AdminStatsRepository:
    """Port satisfied by the Django implementation in infrastructure."""

    def fetch(self) -> AdminStats: ...


def get_admin_stats(repo: AdminStatsRepository) -> AdminStats:
    return repo.fetch()
