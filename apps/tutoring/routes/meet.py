from django.urls import path

from ..views.meet import (
    StudentCancelMeetSessionView,
    StudentMeetSessionDetailView,
    StudentMeetSessionPayView,
    StudentMeetSessionsView,
    TeacherAcceptSessionView,
    TeacherCancelSessionView,
    TeacherCompleteSessionView,
    TeacherMeetSessionDetailView,
    TeacherMeetSessionsView,
    TeacherRejectSessionView,
    TeacherStartSessionView,
)

app_name = "meet"

# tutoring/teacher/urls.py
urlpatterns = [
    path(
        "teacher/meet-sessions/",
        TeacherMeetSessionsView.as_view(),
        name="meet-sessions",
    ),
    path(
        "teacher/meet-sessions/<int:session_id>/",
        TeacherMeetSessionDetailView.as_view(),
        name="meet-session-detail",
    ),
    path(
        "meet-sessions/<int:session_id>/accept/",
        TeacherAcceptSessionView.as_view(),
        name="meet-session-accept",
    ),
    path(
        "meet-sessions/<int:session_id>/reject/",
        TeacherRejectSessionView.as_view(),
        name="meet-session-reject",
    ),
    path(
        "meet-sessions/<int:session_id>/start/",
        TeacherStartSessionView.as_view(),
        name="meet-session-start",
    ),
    path(
        "meet-sessions/<int:session_id>/complete/",
        TeacherCompleteSessionView.as_view(),
        name="meet-session-complete",
    ),
    path(
        "teacher/meet-sessions/<int:session_id>/cancel/",
        TeacherCancelSessionView.as_view(),
        name="meet-session-cancel",
    ),
    path(
        "meet-sessions/",
        StudentMeetSessionsView.as_view(),
        name="student-meet-sessions",
    ),
    path(
        "meet-sessions/<int:session_id>/",
        StudentMeetSessionDetailView.as_view(),
        name="student-meet-session-detail",
    ),
    path(
        "meet-sessions/<int:session_id>/cancel/",
        StudentCancelMeetSessionView.as_view(),
        name="student-meet-session-cancel",
    ),
    path(
        "meet-sessions/<int:session_id>/pay/",
        StudentMeetSessionPayView.as_view(),
        name="meet-session-pay",
    ),
]
