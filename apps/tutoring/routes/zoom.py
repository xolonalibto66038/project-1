from django.urls import path

from ..views.zoom import (  # Teacher; Student
    StudentCancelZoomSessionView,
    StudentZoomSessionDetailView,
    StudentZoomSessionPayView,
    StudentZoomSessionsView,
    TeacherAcceptZoomSessionView,
    TeacherCancelZoomSessionView,
    TeacherCompleteZoomSessionView,
    TeacherRejectZoomSessionView,
    TeacherStartZoomSessionView,
    TeacherZoomSessionDetailView,
    TeacherZoomSessionsView,
)

app_name = "zoom"

urlpatterns = [
    # ── Teacher ───────────────────────────────────────────────────────
    path(
        "teacher/sessions/",
        TeacherZoomSessionsView.as_view(),
        name="zoom-sessions",
    ),
    path(
        "teacher/sessions/<uuid:session_id>/",
        TeacherZoomSessionDetailView.as_view(),
        name="zoom-session-detail",
    ),
    path(
        "teacher/sessions/<uuid:session_id>/accept/",
        TeacherAcceptZoomSessionView.as_view(),
        name="zoom-session-accept",
    ),
    path(
        "teacher/sessions/<uuid:session_id>/reject/",
        TeacherRejectZoomSessionView.as_view(),
        name="zoom-session-reject",
    ),
    path(
        "teacher/sessions/<uuid:session_id>/start/",
        TeacherStartZoomSessionView.as_view(),
        name="zoom-session-start",
    ),
    path(
        "teacher/sessions/<uuid:session_id>/complete/",
        TeacherCompleteZoomSessionView.as_view(),
        name="zoom-session-complete",
    ),
    path(
        "teacher/sessions/<uuid:session_id>/cancel/",
        TeacherCancelZoomSessionView.as_view(),
        name="zoom-session-cancel",
    ),
    # ── Student ───────────────────────────────────────────────────────
    path(
        "student/zoom-sessions/",
        StudentZoomSessionsView.as_view(),
        name="student-zoom-sessions",
    ),
    path(
        "student/zoom-sessions/<uuid:session_id>/",
        StudentZoomSessionDetailView.as_view(),
        name="student-zoom-session-detail",
    ),
    path(
        "student/zoom-sessions/<uuid:session_id>/cancel/",
        StudentCancelZoomSessionView.as_view(),
        name="student-zoom-session-cancel",
    ),
    path(
        "student/zoom-sessions/<uuid:session_id>/pay/",
        StudentZoomSessionPayView.as_view(),
        name="student-zoom-session-pay",
    ),
]
