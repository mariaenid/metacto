"""Feature request use cases."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from ..domain import (
    Description,
    FeatureRequest,
    FeatureRequestNotFound,
    SortOption,
    Title,
)
from .ports import (
    FeatureRequestRepository,
    IdempotencyStore,
    ListPage,
    VoteRepository,
    VoteResult,
)


@dataclass(slots=True)
class FeatureRequestServices:
    requests: FeatureRequestRepository
    votes: VoteRepository
    idempotency: IdempotencyStore


def submit_feature_request(
    services: FeatureRequestServices,
    *,
    title: str,
    description: str,
    author_id: UUID,
) -> FeatureRequest:
    request = FeatureRequest.submit(
        title=Title(title),
        description=Description(description),
        author_id=author_id,
    )
    services.requests.submit_with_author_vote(request)
    return request


def get_feature_request(services: FeatureRequestServices, *, request_id: UUID) -> FeatureRequest:
    request = services.requests.get_by_id(request_id)
    if request is None:
        raise FeatureRequestNotFound(str(request_id))
    return request


def list_feature_requests(
    services: FeatureRequestServices,
    *,
    sort: SortOption,
    limit: int,
    offset: int,
) -> ListPage:
    return services.requests.list(sort=sort, limit=limit, offset=offset)


def cast_vote(
    services: FeatureRequestServices,
    *,
    feature_request_id: UUID,
    user_id: UUID,
    idempotency_key: str | None = None,
) -> VoteResult:
    cached = _load_cached(services, idempotency_key, user_id, "cast", feature_request_id)
    if cached is not None:
        return cached
    if services.requests.get_by_id(feature_request_id) is None:
        raise FeatureRequestNotFound(str(feature_request_id))
    result = services.votes.cast(feature_request_id=feature_request_id, user_id=user_id)
    _store_cached(services, idempotency_key, user_id, "cast", feature_request_id, result)
    return result


def retract_vote(
    services: FeatureRequestServices,
    *,
    feature_request_id: UUID,
    user_id: UUID,
    idempotency_key: str | None = None,
) -> VoteResult:
    cached = _load_cached(services, idempotency_key, user_id, "retract", feature_request_id)
    if cached is not None:
        return cached
    if services.requests.get_by_id(feature_request_id) is None:
        raise FeatureRequestNotFound(str(feature_request_id))
    result = services.votes.retract(feature_request_id=feature_request_id, user_id=user_id)
    _store_cached(services, idempotency_key, user_id, "retract", feature_request_id, result)
    return result


def _idem_key(user_id: UUID, action: str, request_id: UUID, key: str) -> str:
    return f"idem:{action}:{user_id}:{request_id}:{key}"


def _load_cached(
    services: FeatureRequestServices,
    idempotency_key: str | None,
    user_id: UUID,
    action: str,
    request_id: UUID,
) -> VoteResult | None:
    if not idempotency_key:
        return None
    return services.idempotency.get(_idem_key(user_id, action, request_id, idempotency_key))


def _store_cached(
    services: FeatureRequestServices,
    idempotency_key: str | None,
    user_id: UUID,
    action: str,
    request_id: UUID,
    result: VoteResult,
) -> None:
    if not idempotency_key:
        return
    services.idempotency.put(_idem_key(user_id, action, request_id, idempotency_key), result)
