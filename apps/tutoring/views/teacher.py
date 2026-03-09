# apps/tutoring/views/teacher.py

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from apps.authentication.decorators import teacher_required

from ..helpers import convert_to_browser_join_url
from ..models import TutoringSession
from ..services import ZoomService, MeetService


@login_required
@teacher_required
@transaction.atomic
def confirm_session(request, session_id):

    session = TutoringSession.objects.select_for_update().get(
        id=session_id,
        teacher=request.user,
    )

    if session.status != TutoringSession.Status.PAYMENT_AUTHORIZED:
        raise ValidationError("Payment not authorized")

    scheduled_at_str = request.POST["scheduled_at"]

    scheduled_at = parse_datetime(scheduled_at_str)

    if not scheduled_at:
        raise ValidationError("Invalid datetime")

    # make timezone aware (CRITICAL for Zoom)
    scheduled_at = timezone.make_aware(scheduled_at)

    session.scheduled_at = scheduled_at

    meeting = ZoomService.create_meeting(session)

    session.zoom_meeting_id = meeting["id"]
    browser_join_url = convert_to_browser_join_url(meeting["join_url"])
    session.zoom_join_url = browser_join_url
    browser_start_url = convert_to_browser_join_url(meeting["start_url"])
    session.zoom_start_url = browser_start_url

    session.status = TutoringSession.Status.CONFIRMED
    session.confirmed_at = timezone.now()

    session.save()

    return redirect("tutoring:teacher:teacher-sessions")


@login_required
@teacher_required
@transaction.atomic
def confirm_meet_session(request, session_id):

    session = TutoringSession.objects.select_for_update().get(
        id=session_id,
        teacher=request.user,
    )

    if session.status != TutoringSession.Status.PAYMENT_AUTHORIZED:
        raise ValidationError("Payment not authorized")

    scheduled_at_str = request.POST.get("scheduled_at")
    scheduled_at     = parse_datetime(scheduled_at_str)

    if not scheduled_at:
        raise ValidationError("Invalid datetime")

    scheduled_at         = timezone.make_aware(scheduled_at)
    session.scheduled_at = scheduled_at
    session.save(update_fields=['scheduled_at'])  # save before API call

    meeting = MeetService.create_meeting(session)

    session.meeting_id        = meeting['event_id']
    session.meeting_join_url  = meeting['join_url']
    session.meeting_start_url = meeting['start_url']
    session.status            = TutoringSession.Status.CONFIRMED
    session.confirmed_at      = timezone.now()
    session.save()

    return redirect('tutoring:teacher:teacher-sessions')


@login_required
@teacher_required
def teacher_sessions(request):

    sessions = (
        TutoringSession.objects.filter(
            teacher=request.user,
        )
        .select_related("student")
        .order_by("-created_at")
    )

    return render(
        request,
        "apps/tutoring/teacher/teacher_sessions.html",
        {"sessions": sessions},
    )
