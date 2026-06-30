"""Admin stats aggregation queries (Sprint 5). All reads; no writes."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from django.db.models import Count

from ..application.stats_use_cases import AdminStats, TopRequest
from ..domain import ACTIVE_STATUSES, FeatureRequestStatus
from .models import FeatureRequestRecord, StatusChangeLogRecord, VoteRecord

_STALE_UNDER_REVIEW_DAYS = 14


def _now() -> datetime:
    return datetime.now(UTC)


class DjangoAdminStatsRepository:
    def fetch(self) -> AdminStats:
        now = _now()
        cutoff_30d = now - timedelta(days=30)
        stale_cutoff = now - timedelta(days=_STALE_UNDER_REVIEW_DAYS)

        counts_by_status = {s.value: 0 for s in FeatureRequestStatus}
        for row in FeatureRequestRecord.objects.values("status").annotate(n=Count("id")).order_by():
            counts_by_status[row["status"]] = row["n"]

        activity_30d = {
            "submissions": FeatureRequestRecord.objects.filter(created_at__gte=cutoff_30d).count(),
            "votes": VoteRecord.objects.filter(created_at__gte=cutoff_30d).count(),
            "transitions": StatusChangeLogRecord.objects.filter(changed_at__gte=cutoff_30d).count(),
        }

        oldest_open = (
            FeatureRequestRecord.objects.filter(status=FeatureRequestStatus.OPEN.value)
            .order_by("created_at")
            .values_list("created_at", flat=True)
            .first()
        )
        stale_count = FeatureRequestRecord.objects.filter(
            status=FeatureRequestStatus.UNDER_REVIEW.value,
            updated_at__lt=stale_cutoff,
        ).count()
        triage = {
            "oldest_open_at": oldest_open.isoformat() if oldest_open else None,
            "stale_under_review_count": stale_count,
        }

        top_voted = [
            TopRequest(
                id=str(row.id),
                title=row.title,
                vote_count=row.vote_count,
                status=row.status,
            )
            for row in FeatureRequestRecord.objects.filter(
                status__in=[s.value for s in ACTIVE_STATUSES]
            ).order_by("-vote_count")[:10]
        ]

        return AdminStats(
            counts_by_status=counts_by_status,
            activity_30d=activity_30d,
            triage=triage,
            top_voted=top_voted,
        )
