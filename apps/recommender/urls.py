# recommendations/urls.py

from django.urls import path

from .views import (
    CourseResourcesView,
    GradeSubjectResourcesView,
    SimilarCoursesView,
    SimilarResourcesView,
)

app_name = "recommender"


urlpatterns = [
    # ── Similar-item endpoints ─────────────────────────────────────────────
    # "What else is like this resource/course?"
    path(
        "resources/<uuid:pk>/similar/",
        SimilarResourcesView.as_view(),
        name="resource-similar",
    ),
    path(
        "courses/<uuid:pk>/similar/",
        SimilarCoursesView.as_view(),
        name="course-similar",
    ),
    # ── Listing endpoints ──────────────────────────────────────────────────
    # "Show me everything in this course / grade-subject"
    path(
        "courses/<uuid:pk>/resources/",
        CourseResourcesView.as_view(),
        name="course-resources",
    ),
    path(
        "grade-subjects/<uuid:pk>/resources/",
        GradeSubjectResourcesView.as_view(),
        name="grade-subject-resources",
    ),
]
