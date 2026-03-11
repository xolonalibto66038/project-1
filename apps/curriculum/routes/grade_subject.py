from django.urls import path

from ..views import GradeSubjectCoursesByQuarterView, GradeSubjectDetailView

app_name = "grade-subject"

urlpatterns = [
    # without term
    path(
        "grade-subjects/<uuid:pk>/",
        GradeSubjectDetailView.as_view(),
        name="grade-subject-detail",
    ),
    # with term filter
    path(
        "grade-subjects/<uuid:pk>/<str:term>/",
        GradeSubjectDetailView.as_view(),
        name="grade-subject-detail-by-term",
    ),
    path(
        "<uuid:pk>/<str:quarter>/courses/",
        GradeSubjectCoursesByQuarterView.as_view(),
        name="grade-subject-courses-by-quarter",
    ),
]
