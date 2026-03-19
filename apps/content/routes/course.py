from django.urls import path

from ..views.course import (  # CourseCreateView,; CourseDeleteView,; CourseListView,; CourseResourcesView,; CourseUpdateView,
    CourseDetailView,
    CourseExercisesView,
    CourseQuizzesView,
    CourseResourceListView,
    CourseVideosView,
    MarkCourseCompletedView,
)

app_name = "course"

urlpatterns = [
    # path("", CourseListView.as_view(), name="course-list"),
    # path("create/", CourseCreateView.as_view(), name="course-create"),
    path("<uuid:pk>/", CourseDetailView.as_view(), name="course-detail"),
    path(
        "<uuid:pk>/exercises/", CourseExercisesView.as_view(), name="course-exercises"
    ),
    # path(
    #     "<uuid:pk>/resources/", CourseResourcesView.as_view(), name="course-resources"
    # ),
    path(
        "courses/<uuid:pk>/resources/<str:resource_slug>/",
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
    # path("<uuid:pk>/update/", CourseUpdateView.as_view(), name="course-update"),
    # path("<uuid:pk>/delete/", CourseDeleteView.as_view(), name="course-delete"),
    path(
        "<uuid:pk>/quizzes/",
        CourseQuizzesView.as_view(),
        name="course-quizzes-list",
    ),
]
