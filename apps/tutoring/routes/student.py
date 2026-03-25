from django.urls import path

from ..views.student import (
    available_teachers,
    meet_teacher,
    select_teacher,
    session_detail,
    student_sessions,
)
from ..views.teacher import cancel_session, cancel_session_confirm

app_name = "student"

urlpatterns = [
    path(
        "<uuid:subject_pk>/teachers/",
        available_teachers,
        name="available-teachers",
    ),
    path(
        "teachers/<uuid:teacher_id>/select/",
        select_teacher,
        name="select-teacher",
    ),
    path(
        "teachers/<uuid:teacher_id>/meet/",
        meet_teacher,
        name="meet-teacher",
    ),
    path(
        "sessions/",
        student_sessions,
        name="student-sessions",
    ),
    path(
        "sessions/<uuid:session_id>/",
        session_detail,
        name="session-detail",
    ),
    path("sessions/<uuid:session_id>/cancel/", cancel_session, name="cancel-session"),
    path(
        "sessions/<uuid:session_id>/cancel/confirm/",
        cancel_session_confirm,
        name="cancel-session-confirm",
    ),
]
