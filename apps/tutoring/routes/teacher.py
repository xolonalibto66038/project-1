from django.urls import path

from ..views.teacher import confirm_session, confirm_meet_session, teacher_sessions

app_name = "teacher"


urlpatterns = [
    path(
        "sessions/",
        teacher_sessions,
        name="teacher-sessions",
    ),
    path(
        "sessions/<uuid:session_id>/confirm/",
        confirm_session,
        name="confirm-session",
    ),
    path(
        "sessions/<uuid:session_id>/confirm_session/",
        confirm_meet_session,
        name="confirm-meet-session",
    ),
]
