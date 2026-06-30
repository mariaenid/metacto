"""Unified chronological timeline: status log entries + comments (Sprint 6)."""

from __future__ import annotations

from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.comments.infrastructure.models import CommentRecord

from ..infrastructure.models import StatusChangeLogRecord


def _comment_entry(row: CommentRecord) -> dict:
    return {
        "type": "comment",
        "id": str(row.id),
        "author_id": str(row.author_id),
        "body": (
            "[deleted]"
            if row.is_deleted
            else "[hidden by a moderator]"
            if row.is_hidden
            else row.body
        ),
        "is_deleted": row.is_deleted,
        "is_hidden": row.is_hidden,
        "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat(),
    }


def _log_entry(row: StatusChangeLogRecord) -> dict:
    return {
        "type": "status_change",
        "id": str(row.id),
        "from_status": row.from_status,
        "to_status": row.to_status,
        "changed_by_user_id": str(row.changed_by_id),
        "reason": row.reason,
        "changed_at": row.changed_at.isoformat(),
    }


class TimelineView(APIView):
    permission_classes = [AllowAny]

    def get(self, request: Request, request_id) -> Response:
        comments = list(
            CommentRecord.objects.filter(feature_request_id=request_id).order_by("created_at")
        )
        logs = list(
            StatusChangeLogRecord.objects.filter(feature_request_id=request_id).order_by(
                "changed_at"
            )
        )

        # Merge by timestamp into a single chronological stream.
        entries: list[dict] = []
        ci = li = 0
        while ci < len(comments) or li < len(logs):
            take_comment = ci < len(comments) and (
                li >= len(logs) or comments[ci].created_at <= logs[li].changed_at
            )
            if take_comment:
                entries.append(_comment_entry(comments[ci]))
                ci += 1
            else:
                entries.append(_log_entry(logs[li]))
                li += 1

        return Response({"items": entries, "total": len(entries)})
