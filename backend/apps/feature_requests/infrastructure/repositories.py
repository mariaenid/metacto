"""Feature request repository. Hot score is derived in SQL (ADR-03 supersedes the
denormalised hot_score originally proposed in ADR-01)."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from uuid import UUID, uuid4

from django.db import transaction
from django.db.models.expressions import RawSQL

from ..application import ListPage
from ..domain import (
    ACTIVE_STATUSES,
    Description,
    DuplicateCycle,
    FeatureRequest,
    FeatureRequestNotFound,
    FeatureRequestStatus,
    SortOption,
    StatusChangeLog,
    StatusConflict,
    Title,
)
from .models import FeatureRequestRecord, StatusChangeLogRecord, VoteRecord

_HOT_SQL = "(vote_count - 1) / POWER(EXTRACT(EPOCH FROM (NOW() - created_at)) / 86400 + 2, 1.4)"


def _from_record(row: FeatureRequestRecord) -> FeatureRequest:
    return FeatureRequest(
        id=row.id,
        title=Title(row.title),
        description=Description(row.description or ""),
        author_id=row.author_id,
        status=FeatureRequestStatus(row.status),
        vote_count=row.vote_count,
        duplicate_of_id=row.duplicate_of_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class DjangoFeatureRequestRepository:
    def submit_with_author_vote(self, request: FeatureRequest) -> None:
        # RULE-04: author's implicit vote is created in the same transaction as the request.
        with transaction.atomic():
            FeatureRequestRecord.objects.create(
                id=request.id,
                title=request.title.value,
                description=request.description.value,
                author_id=request.author_id,
                status=request.status.value,
                vote_count=1,
            )
            VoteRecord.objects.create(feature_request_id=request.id, user_id=request.author_id)

    def get_by_id(self, request_id: UUID) -> FeatureRequest | None:
        row = FeatureRequestRecord.objects.filter(id=request_id).first()
        return _from_record(row) if row else None

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
        with transaction.atomic():
            # Lock source row to serialize concurrent transitions on the same request.
            row = FeatureRequestRecord.objects.select_for_update().filter(id=request_id).first()
            if row is None:
                raise FeatureRequestNotFound(str(request_id))

            if duplicate_of_id is not None:
                # Lock target; then walk the chain to catch cycles.
                target = (
                    FeatureRequestRecord.objects.select_for_update()
                    .filter(id=duplicate_of_id)
                    .first()
                )
                if target is None:
                    raise FeatureRequestNotFound(str(duplicate_of_id))
                self._assert_no_cycle(request_id=request_id, start_id=duplicate_of_id)

            if FeatureRequestStatus(row.status) is not expected_from:
                raise StatusConflict(
                    f"expected {expected_from.value!r} but current status is {row.status!r}"
                )

            now = datetime.now(UTC)
            FeatureRequestRecord.objects.filter(id=request_id).update(
                status=to_status.value,
                duplicate_of_id=duplicate_of_id,
                updated_at=now,
            )

            log_id = uuid4()
            StatusChangeLogRecord.objects.create(
                id=log_id,
                feature_request_id=request_id,
                from_status=expected_from.value,
                to_status=to_status.value,
                changed_by_id=changed_by_user_id,
                reason=reason,
                changed_at=now,
            )

            refreshed = FeatureRequestRecord.objects.get(id=request_id)
            return (
                _from_record(refreshed),
                StatusChangeLog(
                    id=log_id,
                    feature_request_id=request_id,
                    from_status=expected_from,
                    to_status=to_status,
                    changed_by_user_id=changed_by_user_id,
                    reason=reason,
                    changed_at=now,
                ),
            )

    def _assert_no_cycle(self, *, request_id: UUID, start_id: UUID) -> None:
        # Walk duplicate_of chain from start_id; raise if we reach request_id.
        visited: set[UUID] = set()
        cur: UUID | None = start_id
        while cur is not None:
            if cur == request_id:
                raise DuplicateCycle(
                    f"marking {request_id} as duplicate of {start_id} would create a cycle"
                )
            if cur in visited:
                break  # existing cycle in data — stop to avoid infinite loop
            visited.add(cur)
            cur = (
                FeatureRequestRecord.objects.filter(id=cur)
                .values_list("duplicate_of_id", flat=True)
                .first()
            )

    def list(self, *, sort: SortOption, limit: int, offset: int) -> ListPage:
        queryset = FeatureRequestRecord.objects.all()

        if sort is SortOption.TOP:
            queryset = queryset.filter(status__in=[s.value for s in ACTIVE_STATUSES]).order_by(
                "-vote_count", "-created_at"
            )
        elif sort is SortOption.HOT:
            queryset = queryset.annotate(_hot=RawSQL(_HOT_SQL, [])).order_by(  # noqa: S611
                "-_hot", "-created_at"
            )
        elif sort is SortOption.NEW:
            queryset = queryset.order_by("-created_at")

        total = queryset.count()
        rows = list(queryset[offset : offset + limit])
        items = [_from_record(r) for r in rows]
        return ListPage(items=items, total=total, fingerprint=_fingerprint(items, total))


def _fingerprint(items: list[FeatureRequest], total: int) -> str:
    # Stable hash of (id, vote_count, updated_at, total) so ETag flips on any meaningful change.
    h = hashlib.sha256()
    h.update(str(total).encode())
    for r in items:
        h.update(b"|")
        h.update(str(r.id).encode())
        h.update(b":")
        h.update(str(r.vote_count).encode())
        h.update(b":")
        h.update(r.updated_at.isoformat().encode())
    return h.hexdigest()
