"""Django ORM tables for feature_requests, votes, and status audit log."""
from __future__ import annotations

from uuid import uuid4

from django.db import models
from django.utils import timezone

from ..domain import FeatureRequestStatus


class FeatureRequestRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    author = models.ForeignKey(
        "identity.UserRecord",
        on_delete=models.PROTECT,
        related_name="feature_requests",
    )
    status = models.CharField(
        max_length=16,
        choices=[(s.value, s.value) for s in FeatureRequestStatus],
        default=FeatureRequestStatus.OPEN.value,
        db_index=True,
    )
    vote_count = models.PositiveIntegerField(default=0)
    duplicate_of = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="duplicates",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "feature_request"
        indexes = [
            # Default `top` sort (ADR-01): active statuses ordered by vote_count then recency.
            models.Index(
                fields=["status", "-vote_count", "-created_at"],
                name="idx_fr_top",
            ),
            models.Index(fields=["-created_at"], name="idx_fr_new"),
        ]


class VoteRecord(models.Model):
    """One upvote by a user on a feature request. RULE-01 enforces uniqueness at the DB level."""

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    feature_request = models.ForeignKey(
        FeatureRequestRecord,
        on_delete=models.CASCADE,
        related_name="votes",
    )
    user = models.ForeignKey(
        "identity.UserRecord",
        on_delete=models.CASCADE,
        related_name="votes",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "feature_request_vote"
        constraints = [
            models.UniqueConstraint(
                fields=["feature_request", "user"],
                name="uniq_vote_per_user_per_request",
            ),
        ]


class StatusChangeLogRecord(models.Model):
    """Append-only audit row written atomically with every status transition (RULE-08)."""

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    feature_request = models.ForeignKey(
        FeatureRequestRecord,
        on_delete=models.CASCADE,
        related_name="status_logs",
    )
    from_status = models.CharField(max_length=16)
    to_status = models.CharField(max_length=16)
    changed_by = models.ForeignKey(
        "identity.UserRecord",
        on_delete=models.PROTECT,
        related_name="moderated_status_changes",
    )
    reason = models.TextField(blank=True, null=True)
    changed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "feature_request_status_log"
        indexes = [
            models.Index(
                fields=["feature_request", "-changed_at"],
                name="idx_scl_fr_time",
            ),
        ]
