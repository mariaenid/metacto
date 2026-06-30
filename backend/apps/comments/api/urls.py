"""URL patterns for the comments context."""

from django.urls import path

from .views import CommentDetailView, CommentHideView, CommentListCreateView

urlpatterns = [
    path(
        "feature-requests/<uuid:request_id>/comments",
        CommentListCreateView.as_view(),
        name="comments-list-create",
    ),
    path(
        "comments/<uuid:comment_id>",
        CommentDetailView.as_view(),
        name="comments-detail",
    ),
    path(
        "comments/<uuid:comment_id>/hide",
        CommentHideView.as_view(),
        name="comments-hide",
    ),
]
