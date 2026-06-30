"""ORM table for comments. Soft-delete via is_deleted; moderator suppression via is_hidden."""

from __future__ import annotations

from uuid import uuid4

from django.db import models
from django.utils import timezone


class CommentRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    feature_request = models.ForeignKey(
        "feature_requests.FeatureRequestRecord",
        on_delete=models.CASCADE,
        related_name="comments",
    )
    author = models.ForeignKey(
        "identity.UserRecord",
        on_delete=models.PROTECT,
        related_name="comments",
    )
    body = models.TextField()
    is_deleted = models.BooleanField(default=False)
    is_hidden = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "comment"
        indexes = [
            models.Index(
                fields=["feature_request", "created_at"],
                name="idx_comment_fr_time",
            ),
        ]

    def __str__(self) -> str:
        return f"Comment({self.id})"
