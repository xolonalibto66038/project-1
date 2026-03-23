from django.urls import path

from ..views.course import (
    CourseDetailView,
    CourseQuizzesView,
    CourseResourceListView,
    CourseVideosView,
    MarkCourseCompletedView,
)

app_name = "course"

urlpatterns = [
    path("<uuid:pk>/", CourseDetailView.as_view(), name="course-detail"),
    path(
        "courses/<uuid:pk>/<str:resource_slug>/",
        CourseResourceListView.as_view(),
        name="course-resources",
    ),
    path(
        "<uuid:pk>/videos/",
        CourseVideosView.as_view(),
        name="course-videos",
    ),
    path(
        "<uuid:pk>/mark-completed/",
        MarkCourseCompletedView.as_view(),
        name="course-mark-completed",
    ),
    path(
        "<uuid:pk>/quizzes/",
        CourseQuizzesView.as_view(),
        name="course-quizzes-list",
    ),
]
