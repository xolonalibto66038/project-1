from django.urls import path

from ..views.student import (
    available_teachers,
    select_teacher,
    session_detail,
    student_sessions,
)

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
        "sessions/",
        student_sessions,
        name="student-sessions",
    ),
    path(
        "sessions/<uuid:session_id>/",
        session_detail,
        name="session-detail",
    ),
]
