"""DRF views for feature requests. List/detail are public; submit requires verified email."""
from __future__ import annotations

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from ...identity.api.permissions import IsEmailVerified, IsModerator
from ..application import (
    get_feature_request,
    list_feature_requests,
    submit_feature_request,
)
from ..application.status_use_cases import transition_status
from ..domain import (
    DuplicateCycle,
    DuplicateRequiresTarget,
    FeatureRequestNotFound,
    FeatureRequestStatus,
    InvalidDescription,
    InvalidTitle,
    InvalidTransition,
    SortOption,
    StatusConflict,
)
from ..infrastructure.container import build_services
from .serializers import (
    FeatureRequestListOut,
    FeatureRequestOut,
    StatusChangeLogOut,
    SubmitFeatureRequestIn,
    TransitionStatusIn,
)

DEFAULT_PAGE_SIZE = 25
MAX_PAGE_SIZE = 100


def _list_cache_headers(fingerprint: str) -> dict[str, str]:
    # ETag + stale-while-revalidate per ADR-07. Quote the etag per RFC 7232.
    return {
        "ETag": f'"{fingerprint}"',
        "Cache-Control": "private, max-age=10, stale-while-revalidate=60",
    }


def _detail_cache_headers(updated_at_iso: str, vote_count: int) -> dict[str, str]:
    # Single-row ETag combines updated_at and vote_count so any vote change invalidates the cache.
    import hashlib

    digest = hashlib.sha256(f"{updated_at_iso}:{vote_count}".encode()).hexdigest()
    return {
        "ETag": f'"{digest}"',
        "Cache-Control": "private, max-age=30, stale-while-revalidate=120",
    }


class FeatureRequestListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsEmailVerified()]
        return [AllowAny()]

    def get(self, request: Request) -> Response:
        sort_raw = request.query_params.get("sort", "top")
        try:
            sort = SortOption(sort_raw)
        except ValueError:
            return Response(
                {"detail": f"unknown sort '{sort_raw}'", "code": "invalid_sort"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            limit = min(int(request.query_params.get("limit", DEFAULT_PAGE_SIZE)), MAX_PAGE_SIZE)
            offset = max(int(request.query_params.get("offset", 0)), 0)
        except ValueError:
            return Response(
                {"detail": "limit and offset must be integers", "code": "invalid_pagination"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        page = list_feature_requests(
            build_services(), sort=sort, limit=limit, offset=offset
        )
        headers = _list_cache_headers(page.fingerprint)
        if request.META.get("HTTP_IF_NONE_MATCH") == headers["ETag"]:
            return Response(status=status.HTTP_304_NOT_MODIFIED, headers=headers)

        body = FeatureRequestListOut({"items": page.items, "total": page.total}).data
        return Response(body, headers=headers)

    def post(self, request: Request) -> Response:
        body = SubmitFeatureRequestIn(data=request.data)
        body.is_valid(raise_exception=True)
        try:
            created = submit_feature_request(
                build_services(),
                title=body.validated_data["title"],
                description=body.validated_data.get("description", ""),
                author_id=request.user.id,
            )
        except (InvalidTitle, InvalidDescription) as exc:
            return Response(
                {"detail": str(exc), "code": "invalid_input"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(FeatureRequestOut(created).data, status=status.HTTP_201_CREATED)


class FeatureRequestDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request: Request, request_id) -> Response:
        try:
            fr = get_feature_request(build_services(), request_id=request_id)
        except FeatureRequestNotFound:
            return Response(
                {"detail": "Feature request not found", "code": "not_found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        headers = _detail_cache_headers(fr.updated_at.isoformat(), fr.vote_count)
        if request.META.get("HTTP_IF_NONE_MATCH") == headers["ETag"]:
            return Response(status=status.HTTP_304_NOT_MODIFIED, headers=headers)
        return Response(FeatureRequestOut(fr).data, headers=headers)


class StatusTransitionView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsModerator]

    def patch(self, request: Request, request_id) -> Response:
        body = TransitionStatusIn(data=request.data)
        body.is_valid(raise_exception=True)
        d = body.validated_data
        try:
            fr, log = transition_status(
                build_services(),
                request_id=request_id,
                expected_from=FeatureRequestStatus(d["expected_from"]),
                to_status=FeatureRequestStatus(d["to_status"]),
                changed_by_user_id=request.user.id,
                reason=d.get("reason"),
                duplicate_of_id=d.get("duplicate_of_id"),
            )
        except FeatureRequestNotFound:
            return Response(
                {"detail": "Feature request not found", "code": "not_found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except InvalidTransition:
            return Response(
                {"detail": "Transition not allowed by state machine", "code": "invalid_transition"},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        except DuplicateRequiresTarget:
            return Response(
                {"detail": "duplicate_of_id required when transitioning to duplicate", "code": "duplicate_requires_target"},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        except DuplicateCycle:
            return Response(
                {"detail": "Would create a duplicate cycle", "code": "duplicate_cycle"},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        except StatusConflict as exc:
            return Response(
                {"detail": str(exc), "code": "status_conflict"},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(
            {"feature_request": FeatureRequestOut(fr).data, "log": StatusChangeLogOut(log).data}
        )
