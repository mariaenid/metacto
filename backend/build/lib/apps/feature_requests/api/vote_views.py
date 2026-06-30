"""Vote toggle endpoints. Cast = POST, retract = DELETE. Both idempotent (RULE-10)."""
from __future__ import annotations

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from ...identity.api.permissions import IsEmailVerified
from ..application import cast_vote, retract_vote
from ..domain import FeatureRequestNotFound
from ..infrastructure.container import build_services
from .serializers_vote import VoteOut


def _idempotency_key(request: Request) -> str | None:
    return request.META.get("HTTP_IDEMPOTENCY_KEY")


class VoteView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified]

    def post(self, request: Request, request_id) -> Response:
        try:
            result = cast_vote(
                build_services(),
                feature_request_id=request_id,
                user_id=request.user.id,
                idempotency_key=_idempotency_key(request),
            )
        except FeatureRequestNotFound:
            return Response(
                {"detail": "Feature request not found", "code": "not_found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(VoteOut(result).data, status=status.HTTP_200_OK)

    def delete(self, request: Request, request_id) -> Response:
        try:
            result = retract_vote(
                build_services(),
                feature_request_id=request_id,
                user_id=request.user.id,
                idempotency_key=_idempotency_key(request),
            )
        except FeatureRequestNotFound:
            return Response(
                {"detail": "Feature request not found", "code": "not_found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(VoteOut(result).data, status=status.HTTP_200_OK)
