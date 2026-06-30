"""Root URL configuration. App routers are mounted under /v1."""

from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("v1/", include("apps.identity.api.urls")),
    path("v1/", include("apps.feature_requests.api.urls")),
    path("v1/", include("apps.comments.api.urls")),
    path("v1/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("v1/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
]
