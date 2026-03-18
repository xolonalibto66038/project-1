# apps/tutoring/views/teacher.py

from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.http import require_POST

from apps.authentication.decorators import teacher_required

from ..helpers import convert_to_browser_join_url, redirect_back
from ..models import TutoringSession
from ..services import MeetService, ZoomService


@login_required
def cancel_session_confirm(request, session_id):
    """Show the irreversible warning page before actual cancellation."""

    if request.user.is_teacher:
        lookup = {"id": session_id, "teacher": request.user}
    else:
        lookup = {"id": session_id, "student": request.user}

    session = get_object_or_404(TutoringSession, **lookup)

    cancellable_statuses = [
        TutoringSession.Status.PAYMENT_AUTHORIZED,
        TutoringSession.Status.CONFIRMED,
    ]

    if session.status not in cancellable_statuses:
        messages.error(request, "This session cannot be canceled at this stage.")
        if request.user.is_teacher:
            return redirect("tutoring:teacher:teacher-sessions")
        return redirect("tutoring:student:student-sessions")

    cancel_url = (
        "teacher:cancel-session"
        if request.user.is_teacher
        else "student:cancel-session"
    )

    return render(
        request,
        "apps/tutoring/cancel_confirm.html",
        {
            "session": session,
            "cancel_url": cancel_url,
        },
    )


@login_required
@require_POST
@transaction.atomic
def cancel_session(request, session_id):

    if request.user.is_teacher:
        lookup = {"id": session_id, "teacher": request.user}
    else:
        lookup = {"id": session_id, "student": request.user}

    session = get_object_or_404(
        TutoringSession.objects.select_for_update(),
        **lookup,
    )

    cancellable_statuses = [
        TutoringSession.Status.PAYMENT_AUTHORIZED,
        TutoringSession.Status.CONFIRMED,
    ]

    if session.status not in cancellable_statuses:
        messages.error(request, "This session cannot be canceled at this stage.")
        if request.user.is_teacher:
            return redirect("tutoring:teacher:teacher-sessions")
        return redirect("tutoring:student:student-sessions")

    # Cancel Zoom meeting if exists
    if session.zoom_meeting_id:
        try:
            ZoomService.delete_meeting(session.zoom_meeting_id)
        except Exception as ex:
            print(f"Zoom delete failed: {str(ex)}")

    session.status = TutoringSession.Status.CANCELED
    session.canceled_by = request.user  # ← who canceled
    session.save(update_fields=["status", "canceled_by", "updated_at"])

    # TODO: trigger refund if session was paid
    # refund_session.delay(session.id)

    messages.success(request, "Session has been canceled.")

    if request.user.is_teacher:
        return redirect("tutoring:teacher:teacher-sessions")
    return redirect("tutoring:student:student-sessions")


# @login_required
# @require_POST
# @transaction.atomic
# def cancel_session(request, session_id):

#     # Build query based on role — teacher or student
#     if request.user.is_teacher:
#         lookup = {"id": session_id, "teacher": request.user}
#     else:
#         lookup = {"id": session_id, "student": request.user}

#     session = get_object_or_404(
#         TutoringSession.objects.select_for_update(),
#         **lookup,
#     )

#     # Only cancellable if not already done or canceled
#     cancellable_statuses = [
#         TutoringSession.Status.PAYMENT_AUTHORIZED,
#         TutoringSession.Status.CONFIRMED,
#     ]

#     if session.status not in cancellable_statuses:
#         messages.error(request, "This session cannot be canceled at this stage.")
#         return redirect_back(request)

#     # Cancel Zoom meeting if one exists
#     if session.zoom_meeting_id:
#         try:
#             ZoomService.delete_meeting(session.zoom_meeting_id)
#         except Exception as ex:
#             # Log but don't block cancellation
#             print(f"Zoom delete failed: {str(ex)}")

#     session.status = TutoringSession.Status.CANCELED
#     session.save(update_fields=["status", "updated_at"])

#     # TODO: trigger refund if session was paid
#     # refund_session.delay(session.id)

#     messages.success(request, "Session has been canceled.")

#     if request.user.is_teacher:
#         return redirect("tutoring:teacher:teacher-sessions")
#     else:
#         return redirect("tutoring:student:student-sessions")


# @login_required
# @teacher_required
# @transaction.atomic
# def confirm_session(request, session_id):

#     session = TutoringSession.objects.select_for_update().get(
#         id=session_id,
#         teacher=request.user,
#     )

#     if session.status != TutoringSession.Status.PAYMENT_AUTHORIZED:
#         raise ValidationError("Payment not authorized")

#     scheduled_at_str = request.POST["scheduled_at"]

#     scheduled_at = parse_datetime(scheduled_at_str)

#     if not scheduled_at:
#         raise ValidationError("Invalid datetime")

#     # make timezone aware (CRITICAL for Zoom)
#     scheduled_at = timezone.make_aware(scheduled_at)

#     session.scheduled_at = scheduled_at

#     meeting = ZoomService.create_meeting(session)

#     session.zoom_meeting_id = meeting["id"]
#     browser_join_url = convert_to_browser_join_url(meeting["join_url"])
#     session.zoom_join_url = browser_join_url
#     browser_start_url = convert_to_browser_join_url(meeting["start_url"])
#     session.zoom_start_url = browser_start_url

#     session.status = TutoringSession.Status.CONFIRMED
#     session.confirmed_at = timezone.now()

#     session.save()

#     return redirect("tutoring:teacher:teacher-sessions")


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

    scheduled_at = timezone.make_aware(scheduled_at)

    # ── Overlap check ─────────────────────────────────────────────────────────
    # Each session is 60 min + 30 min buffer = 90 min between sessions
    buffer = timedelta(minutes=90)
    conflict = (
        TutoringSession.objects.filter(
            teacher=request.user,
            status__in=[
                TutoringSession.Status.CONFIRMED,
                TutoringSession.Status.IN_PROGRESS,
            ],
            scheduled_at__range=(
                scheduled_at - buffer,
                scheduled_at + buffer,
            ),
        )
        .exclude(id=session.id)
        .exists()
    )

    if conflict:
        messages.error(
            request,
            "This time slot is unavailable. Please leave at least 1.5 hours between sessions.",
        )
        return redirect("tutoring:teacher:teacher-sessions")
    # ──────────────────────────────────────────────────────────────────────────

    session.scheduled_at = scheduled_at

    meeting = ZoomService.create_meeting(session)

    session.zoom_meeting_id = meeting["id"]
    session.zoom_join_url = convert_to_browser_join_url(meeting["join_url"])
    session.zoom_start_url = convert_to_browser_join_url(meeting["start_url"])
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
    scheduled_at = parse_datetime(scheduled_at_str)

    if not scheduled_at:
        raise ValidationError("Invalid datetime")

    scheduled_at = timezone.make_aware(scheduled_at)
    session.scheduled_at = scheduled_at
    session.save(update_fields=["scheduled_at"])  # save before API call

    meeting = MeetService.create_meeting(session)

    session.meeting_id = meeting["event_id"]
    session.meeting_join_url = meeting["join_url"]
    session.meeting_start_url = meeting["start_url"]
    session.status = TutoringSession.Status.CONFIRMED
    session.confirmed_at = timezone.now()
    session.save()

    return redirect("tutoring:teacher:teacher-sessions")


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
