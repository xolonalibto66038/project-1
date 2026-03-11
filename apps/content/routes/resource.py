from django.urls import path

from ..views.resource import ResourceDetailView, resource_download_view

app_name = "resource"

urlpatterns = [
    path("<uuid:pk>/", ResourceDetailView.as_view(), name="resource-detail"),
    path("<uuid:pk>/download/", resource_download_view, name="resource-download"),
]
