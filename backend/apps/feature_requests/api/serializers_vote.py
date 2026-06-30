"""Output shape for vote toggle responses."""

from __future__ import annotations

from rest_framework import serializers


class VoteOut(serializers.Serializer):
    feature_request_id = serializers.UUIDField()
    voted = serializers.BooleanField()
    vote_count = serializers.IntegerField()
