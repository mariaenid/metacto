"""Admin stats endpoint. Gated by IsAdmin (Sprint 5)."""

from __future__ import annotations

from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from ...identity.api.permissions import IsAdmin
from ..application.stats_use_cases import get_admin_stats
from ..infrastructure.stats_repository import DjangoAdminStatsRepository


class _TopRequestOut(serializers.Serializer):
    id = serializers.CharField()
    title = serializers.CharField()
    vote_count = serializers.IntegerField()
    status = serializers.CharField()


class _AdminStatsOut(serializers.Serializer):
    counts_by_status = serializers.DictField(child=serializers.IntegerField())
    activity_30d = serializers.DictField(child=serializers.IntegerField())
    triage = serializers.DictField()
    top_voted = _TopRequestOut(many=True)


class AdminStatsView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request: Request) -> Response:
        stats = get_admin_stats(DjangoAdminStatsRepository())
        return Response(_AdminStatsOut(stats).data)
