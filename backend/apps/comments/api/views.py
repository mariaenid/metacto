"""Comment views: post, list, edit, delete, moderator-hide."""

from __future__ import annotations

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from ...identity.api.permissions import IsEmailVerified, IsModerator
from ..application import (
    delete_comment,
    edit_comment,
    list_comments,
    moderator_hide_comment,
    post_comment,
)
from ..domain import (
    CommentNotEditable,
    CommentNotFound,
    InvalidBody,
    NotCommentAuthor,
)
from ..infrastructure.container import build_comment_services
from .serializers import CommentListOut, CommentOut, EditCommentIn, PostCommentIn


class _CommentPostThrottle(UserRateThrottle):
    # Per-user rate limit on creating comments (ADR-07).
    scope = "comment_post"
    rate = "30/hour"


class CommentListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsEmailVerified()]
        return [AllowAny()]

    def get_throttles(self):
        if self.request.method == "POST":
            return [_CommentPostThrottle()]
        return []

    def get(self, request: Request, request_id) -> Response:
        try:
            limit = min(int(request.query_params.get("limit", 50)), 200)
            offset = max(int(request.query_params.get("offset", 0)), 0)
        except ValueError:
            return Response(
                {"detail": "limit and offset must be integers", "code": "invalid_pagination"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        page = list_comments(
            build_comment_services(),
            feature_request_id=request_id,
            limit=limit,
            offset=offset,
        )
        return Response(CommentListOut({"items": page.items, "total": page.total}).data)

    def post(self, request: Request, request_id) -> Response:
        body = PostCommentIn(data=request.data)
        body.is_valid(raise_exception=True)
        try:
            comment = post_comment(
                build_comment_services(),
                feature_request_id=request_id,
                author_id=request.user.id,
                body=body.validated_data["body"],
            )
        except InvalidBody as exc:
            return Response(
                {"detail": str(exc), "code": "invalid_body"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(CommentOut(comment).data, status=status.HTTP_201_CREATED)


class CommentDetailView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified]

    def patch(self, request: Request, comment_id) -> Response:
        body = EditCommentIn(data=request.data)
        body.is_valid(raise_exception=True)
        try:
            comment = edit_comment(
                build_comment_services(),
                comment_id=comment_id,
                editor_id=request.user.id,
                body=body.validated_data["body"],
            )
        except CommentNotFound:
            return Response(
                {"detail": "Comment not found", "code": "not_found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except NotCommentAuthor:
            return Response(
                {"detail": "You are not the author of this comment", "code": "not_author"},
                status=status.HTTP_403_FORBIDDEN,
            )
        except CommentNotEditable as exc:
            return Response(
                {"detail": str(exc), "code": "not_editable"},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        except InvalidBody as exc:
            return Response(
                {"detail": str(exc), "code": "invalid_body"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(CommentOut(comment).data)

    def delete(self, request: Request, comment_id) -> Response:
        user = request.user
        is_mod = getattr(user, "role", "") in ("moderator", "admin")
        try:
            delete_comment(
                build_comment_services(),
                comment_id=comment_id,
                requester_id=user.id,
                is_moderator=is_mod,
            )
        except CommentNotFound:
            return Response(
                {"detail": "Comment not found", "code": "not_found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except NotCommentAuthor:
            return Response(
                {"detail": "You are not the author of this comment", "code": "not_author"},
                status=status.HTTP_403_FORBIDDEN,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class CommentHideView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsModerator]

    def post(self, request: Request, comment_id) -> Response:
        try:
            comment = moderator_hide_comment(build_comment_services(), comment_id=comment_id)
        except CommentNotFound:
            return Response(
                {"detail": "Comment not found", "code": "not_found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(CommentOut(comment).data)
