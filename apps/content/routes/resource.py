from django.urls import path

from ..views.resource import (
    ResourceCreateView,
    ResourceDeleteView,
    ResourceDetailView,
    ResourceUpdateView,
    TeacherResourceDetailView,
    TeacherResourceListView,
    resource_download_view,
)

app_name = "resource"

urlpatterns = [
    path("<uuid:pk>/", ResourceDetailView.as_view(), name="resource-detail"),
    path("<uuid:pk>/download/", resource_download_view, name="resource-download"),
    path(
        "my-resources/", TeacherResourceListView.as_view(), name="teacher-resource-list"
    ),
    path("create/", ResourceCreateView.as_view(), name="resource-create"),
    path(
        "<uuid:pk>/teacher/",
        TeacherResourceDetailView.as_view(),
        name="teacher-resource-detail",
    ),
    path("<uuid:pk>/edit/", ResourceUpdateView.as_view(), name="resource-update"),
    path("<uuid:pk>/delete/", ResourceDeleteView.as_view(), name="resource-delete"),
]
