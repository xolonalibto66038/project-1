from django.urls import path

from ..views import (
    SubjectCoursesByQuarterView,
    SubjectDetailView,
    SubjectResourceListView,
)

app_name = "subject"

urlpatterns = [
    # path("", SubjectListView.as_view(), name="subject-list"),
    # path("create/", SubjectCreateView.as_view(), name="subject-create"),
    path("<uuid:pk>/", SubjectDetailView.as_view(), name="subject-detail"),
    # path("<uuid:pk>/update/", SubjectUpdateView.as_view(), name="subject-update"),
    # path("<uuid:pk>/delete/", SubjectDeleteView.as_view(), name="subject-delete"),
    path(
        "<uuid:pk>/<str:quarter>/courses/",
        SubjectCoursesByQuarterView.as_view(),
        name="subject-courses-by-quarter",
    ),
    path(
        "subjects/<uuid:pk>/resources/<str:resource_slug>/",
        SubjectResourceListView.as_view(),
        name="subject-resources",
    ),
]
