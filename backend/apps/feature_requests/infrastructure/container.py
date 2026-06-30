"""Wires concrete adapters into FeatureRequestServices."""

from __future__ import annotations

from ..application import FeatureRequestServices
from .idempotency import CachedIdempotencyStore
from .repositories import DjangoFeatureRequestRepository
from .vote_repository import DjangoVoteRepository


def build_services() -> FeatureRequestServices:
    return FeatureRequestServices(
        requests=DjangoFeatureRequestRepository(),
        votes=DjangoVoteRepository(),
        idempotency=CachedIdempotencyStore(),
    )
