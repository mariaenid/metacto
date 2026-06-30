"""Serializers for the feature_requests API."""

from __future__ import annotations

from rest_framework import serializers

from ..domain import FeatureRequestStatus

_STATUS_CHOICES = [s.value for s in FeatureRequestStatus]


class SubmitFeatureRequestIn(serializers.Serializer):
    title = serializers.CharField(min_length=1, max_length=200)
    description = serializers.CharField(
        max_length=5000, allow_blank=True, required=False, default=""
    )


class FeatureRequestOut(serializers.Serializer):
    id = serializers.UUIDField()
    title = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    author_id = serializers.UUIDField()
    status = serializers.SerializerMethodField()
    vote_count = serializers.IntegerField()
    duplicate_of_id = serializers.UUIDField(allow_null=True)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()

    def get_title(self, obj) -> str:
        return obj.title.value

    def get_description(self, obj) -> str:
        return obj.description.value

    def get_status(self, obj) -> str:
        return obj.status.value


class FeatureRequestListOut(serializers.Serializer):
    items = FeatureRequestOut(many=True)
    total = serializers.IntegerField()


class TransitionStatusIn(serializers.Serializer):
    expected_from = serializers.ChoiceField(choices=_STATUS_CHOICES)
    to_status = serializers.ChoiceField(choices=_STATUS_CHOICES)
    reason = serializers.CharField(
        max_length=500, allow_blank=True, allow_null=True, required=False
    )
    duplicate_of_id = serializers.UUIDField(allow_null=True, required=False)


class StatusChangeLogOut(serializers.Serializer):
    id = serializers.UUIDField()
    feature_request_id = serializers.UUIDField()
    from_status = serializers.SerializerMethodField()
    to_status = serializers.SerializerMethodField()
    changed_by_user_id = serializers.UUIDField()
    reason = serializers.CharField(allow_null=True)
    changed_at = serializers.DateTimeField()

    def get_from_status(self, obj) -> str:
        return obj.from_status.value

    def get_to_status(self, obj) -> str:
        return obj.to_status.value


class StatusTransitionOut(serializers.Serializer):
    feature_request = FeatureRequestOut()
    log = StatusChangeLogOut()
