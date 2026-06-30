"""Serializers for the comments API."""

from __future__ import annotations

from rest_framework import serializers


class PostCommentIn(serializers.Serializer):
    body = serializers.CharField(min_length=1, max_length=5000)


class EditCommentIn(serializers.Serializer):
    body = serializers.CharField(min_length=1, max_length=5000)


class CommentOut(serializers.Serializer):
    id = serializers.UUIDField()
    feature_request_id = serializers.UUIDField()
    author_id = serializers.UUIDField()
    body = serializers.SerializerMethodField()
    is_deleted = serializers.BooleanField()
    is_hidden = serializers.BooleanField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()

    def get_body(self, obj) -> str:
        return obj.display_body()


class CommentListOut(serializers.Serializer):
    items = CommentOut(many=True)
    total = serializers.IntegerField()
