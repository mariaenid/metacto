"""Feature request endpoints."""
from django.urls import path

from .views import FeatureRequestDetailView, FeatureRequestListCreateView, StatusTransitionView
from .vote_views import VoteView

urlpatterns = [
    path(
        "feature-requests",
        FeatureRequestListCreateView.as_view(),
        name="feature-requests-list-create",
    ),
    path(
        "feature-requests/<uuid:request_id>",
        FeatureRequestDetailView.as_view(),
        name="feature-requests-detail",
    ),
    path(
        "feature-requests/<uuid:request_id>/vote",
        VoteView.as_view(),
        name="feature-requests-vote",
    ),
    path(
        "feature-requests/<uuid:request_id>/status",
        StatusTransitionView.as_view(),
        name="feature-requests-status",
    ),
]
