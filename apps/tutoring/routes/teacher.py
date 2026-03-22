from django.urls import path

from ..views.teacher import (  # confirm_meet_session,
    cancel_session,
    cancel_session_confirm,
    confirm_session,
    teacher_sessions,
)

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
    # path(
    #     "sessions/<uuid:session_id>/confirm_session/",
    #     confirm_meet_session,
    #     name="confirm-meet-session",
    # ),
    path("sessions/<uuid:session_id>/cancel/", cancel_session, name="cancel-session"),
    path(
        "sessions/<uuid:session_id>/cancel/confirm/",
        cancel_session_confirm,
        name="cancel-session-confirm",
    ),
]
