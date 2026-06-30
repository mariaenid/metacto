"""Concurrency-safe vote toggling. The Vote row is the source of truth;
FeatureRequest.vote_count is a denormalised cache maintained atomically (ADR-03)."""

from __future__ import annotations

from uuid import UUID

from django.db import IntegrityError, transaction
from django.db.models import F

from ..application import VoteResult
from .models import FeatureRequestRecord, VoteRecord


class DjangoVoteRepository:
    def cast(self, *, feature_request_id: UUID, user_id: UUID) -> VoteResult:
        try:
            with transaction.atomic():
                VoteRecord.objects.create(feature_request_id=feature_request_id, user_id=user_id)
                FeatureRequestRecord.objects.filter(id=feature_request_id).update(
                    vote_count=F("vote_count") + 1
                )
        except IntegrityError:
            # Unique constraint on (feature_request, user) means the user already voted.
            # Re-read the current count and report idempotently.
            pass
        return self._snapshot(feature_request_id, user_id)

    def retract(self, *, feature_request_id: UUID, user_id: UUID) -> VoteResult:
        with transaction.atomic():
            deleted, _ = VoteRecord.objects.filter(
                feature_request_id=feature_request_id, user_id=user_id
            ).delete()
            if deleted:
                FeatureRequestRecord.objects.filter(id=feature_request_id).update(
                    vote_count=F("vote_count") - 1
                )
        return self._snapshot(feature_request_id, user_id)

    def _snapshot(self, feature_request_id: UUID, user_id: UUID) -> VoteResult:
        row = FeatureRequestRecord.objects.only("id", "vote_count").get(id=feature_request_id)
        voted = VoteRecord.objects.filter(
            feature_request_id=feature_request_id, user_id=user_id
        ).exists()
        return VoteResult(feature_request_id=row.id, voted=voted, vote_count=row.vote_count)
