from django.urls import path

from ..views import (  # GradeSubjectResourceListView,
    GradeSubjectCoursesByQuarterView,
    GradeSubjectDetailView,
    GradeSubjectResourceListByTermView,
    GradeSubjectQuizzesView
)

app_name = "grade-subject"

urlpatterns = [
    # without term
    path(
        "grade-subjects/<uuid:pk>/",
        GradeSubjectDetailView.as_view(),
        name="grade-subject-detail",
    ),
    # with term filter
    # path(
    #     "grade-subjects/<uuid:pk>/<str:term>/",
    #     GradeSubjectDetailView.as_view(),
    #     name="grade-subject-detail-by-term",
    # ),
    path(
        "<uuid:pk>/<str:quarter>/courses/",
        GradeSubjectCoursesByQuarterView.as_view(),
        name="grade-subject-courses-by-quarter",
    ),
    # path(
    #     "subjects/<uuid:pk>/resources/<str:resource_slug>/",
    #     GradeSubjectResourceListView.as_view(),
    #     name="grade-subject-resources",
    # ),
    path(
        "grade-subjects/<uuid:pk>/resources/",
        GradeSubjectResourceListByTermView.as_view(),
        name="grade-subject-resource-list",
    ),
    path(
        "grade-subjects/<uuid:pk>/resources/<str:resource_slug>/<str:term>/",
        GradeSubjectResourceListByTermView.as_view(),
        name="grade-subject-resource-list-by-term",
    ),
    path(
        "grade-subjects/<uuid:pk>/quizzes/",
        GradeSubjectQuizzesView.as_view(),
        name="grade-subject-quizzes-list",
    ),

]
