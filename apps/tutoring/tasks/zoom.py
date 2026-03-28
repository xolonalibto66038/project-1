# apps/tutoring/tasks/zoom.py

import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


# ── Notifications ──────────────────────────────────────────────────────────────


@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def notify_teacher_new_request(self, session_pk: int):
    from ..models import ZoomSession

    try:
        session = ZoomSession.objects.select_related("student", "teacher").get(
            pk=session_pk
        )
        send_mail(
            subject=f"New tutoring request from {session.student.get_full_name()}",
            message=(
                f"Hi {session.teacher.first_name},\n\n"
                f"{session.student.get_full_name()} has requested a tutoring session on "
                f"{session.proposed_start.strftime('%A %d %B %Y at %H:%M UTC')} "
                f"({session.duration_minutes} min).\n\n"
                f"Log in to review and accept or decline the request."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[session.teacher.email],
        )
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def notify_student_pending_payment(self, session_pk: int):
    from ..models import ZoomSession

    try:
        session = ZoomSession.objects.select_related("student", "teacher").get(
            pk=session_pk
        )
        pay_url = (
            f"{settings.FRONTEND_BASE_URL}/tutoring/student/sessions/{session.pk}/pay/"
        )
        send_mail(
            subject="Your session has been approved — complete your payment",
            message=(
                f"Hi {session.student.first_name},\n\n"
                f"{session.teacher.get_full_name()} has accepted your session request.\n\n"
                f"Complete your payment to confirm the session:\n{pay_url}\n\n"
                f"Amount due: {session.price} {session.price_currency}\n"
                f"Session date: {session.proposed_start.strftime('%A %d %B %Y at %H:%M UTC')}"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[session.student.email],
        )
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task
def notify_student_rejected(session_pk: int):
    from ..models import ZoomSession

    session = ZoomSession.objects.select_related("student", "teacher").get(
        pk=session_pk
    )
    send_mail(
        subject="Your session request was declined",
        message=(
            f"Hi {session.student.first_name},\n\n"
            f"Unfortunately {session.teacher.get_full_name()} couldn't accept your request.\n"
            f"Reason: {session.cancellation_reason or 'Not specified'}\n\n"
            f"Browse other available teachers on the platform."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[session.student.email],
    )


@shared_task
def notify_student_payment_failed(session_pk: int):
    from ..models import ZoomSession

    session = ZoomSession.objects.select_related("student", "teacher").get(
        pk=session_pk
    )
    pay_url = (
        f"{settings.FRONTEND_BASE_URL}/tutoring/student/sessions/{session.pk}/pay/"
    )
    send_mail(
        subject="Payment failed for your tutoring session",
        message=(
            f"Hi {session.student.first_name},\n\n"
            f"Your payment for the session with {session.teacher.get_full_name()} on "
            f"{session.proposed_start.strftime('%A %d %B %Y at %H:%M UTC')} did not go through.\n\n"
            f"Please retry your payment here:\n{pay_url}\n\n"
            f"If the issue persists, contact support."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[session.student.email],
    )


# ── Zoom meeting provisioning retry ───────────────────────────────────────────


@shared_task(bind=True, max_retries=5, default_retry_delay=300)
def retry_create_zoom_meeting(self, session_pk: int):
    """
    Fallback task if Zoom meeting creation failed during webhook processing.
    Retries up to 5 times with a 5-minute delay between attempts.
    Once the meeting is provisioned it transitions the session to CONFIRMED
    and schedules all time-based tasks.
    """
    from ..helpers import ZoomError, create_zoom_meeting
    from ..models import ZoomSession
    from ..services.zoom import _schedule_session_tasks

    try:
        session = ZoomSession.objects.get(pk=session_pk)

        # Already fixed by a previous retry or concurrent call
        if session.zoom_meeting_id:
            logger.info(
                "retry_create_zoom_meeting: session %s already has a meeting, skipping.",
                session_pk,
            )
            return

        zoom_data = create_zoom_meeting(session)

        session.confirm(
            zoom_meeting_id=zoom_data["meeting_id"],
            zoom_join_url=zoom_data["join_url"],
            zoom_start_url=zoom_data["start_url"],
            zoom_password=zoom_data.get("password"),
        )
        session.save()

        _schedule_session_tasks(session)

        logger.info(
            "retry_create_zoom_meeting: session %s confirmed with meeting %s.",
            session_pk,
            zoom_data["meeting_id"],
        )

    except ZoomError as exc:
        logger.warning(
            "retry_create_zoom_meeting: ZoomError for session %s — %s",
            session_pk,
            exc,
        )
        raise self.retry(exc=exc)

    except Exception as exc:
        raise self.retry(exc=exc)


# ── Session lifecycle tasks ────────────────────────────────────────────────────


@shared_task(bind=True, max_retries=3)
def send_session_reminder(self, session_pk: int, window: str):
    """
    Send a pre-session reminder to both participants.
    `window` is either '1h' or '15m'.
    """
    from ..models import ZoomSession

    try:
        session = ZoomSession.objects.select_related("student", "teacher").get(
            pk=session_pk
        )

        # Abort if the session is no longer going ahead
        if session.state not in (
            ZoomSession.State.CONFIRMED,
            ZoomSession.State.IN_PROGRESS,
        ):
            logger.info(
                "send_session_reminder: session %s is in state '%s', skipping reminder.",
                session_pk,
                session.state,
            )
            return

        label = "1 hour" if window == "1h" else "15 minutes"

        for recipient in [session.student, session.teacher]:
            send_mail(
                subject=f"Your tutoring session starts in {label}",
                message=(
                    f"Hi {recipient.first_name},\n\n"
                    f"Reminder: your tutoring session starts in {label}.\n\n"
                    f"Date: {session.confirmed_start.strftime('%A %d %B %Y at %H:%M UTC')}\n"
                    f"Join Zoom: {session.zoom_join_url}\n"
                    f"Password: {session.zoom_password}"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient.email],
            )

    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3)
def auto_complete_session(self, session_pk: int):
    """
    Automatically mark a session as completed 15 minutes after its expected end.
    If the teacher never hit Start, we push through IN_PROGRESS first.
    """
    from ..models import ZoomSession
    from ..services.zoom import ZoomService

    try:
        session = ZoomSession.objects.get(pk=session_pk)

        if session.state == ZoomSession.State.IN_PROGRESS:
            ZoomService.complete_session(session)

        elif session.state == ZoomSession.State.CONFIRMED:
            # Teacher never manually started the session — still count it
            session.start()
            session.save()
            ZoomService.complete_session(session)

        else:
            logger.info(
                "auto_complete_session: session %s is in state '%s', nothing to do.",
                session_pk,
                session.state,
            )

    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task
def request_student_review(session_pk: int):
    from ..models import ZoomSession

    session = ZoomSession.objects.select_related("student", "teacher").get(
        pk=session_pk
    )
    review_url = (
        f"{settings.FRONTEND_BASE_URL}/tutoring/student/sessions/{session.pk}/review/"
    )
    send_mail(
        subject=f"How was your session with {session.teacher.get_full_name()}?",
        message=(
            f"Hi {session.student.first_name},\n\n"
            f"We hope your tutoring session with {session.teacher.get_full_name()} went well!\n\n"
            f"Leave a review to help other students:\n{review_url}"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[session.student.email],
    )


# @shared_task(name="apps.tutoring.tasks.cleanup_unpaid_sessions")
# def cleanup_unpaid_sessions():
#     from datetime import timedelta

#     from django.utils import timezone

#     from apps.tutoring.models import TutoringSession

#     now = timezone.now()

#     deleted_count, _ = TutoringSession.objects.filter(
#         status__in=[
#             TutoringSession.Status.PENDING_PAYMENT,
#             TutoringSession.Status.PAYMENT_FAILED,
#         ],
#         scheduled_at__lt=now - timedelta(hours=1),
#     ).delete()

#     return f"Deleted {deleted_count} unpaid/failed sessions"


# @shared_task(name="apps.tutoring.tasks.cancel_noshow_sessions")
# def cancel_noshow_sessions():
#     from datetime import timedelta

#     from django.utils import timezone

#     from apps.tutoring.models import TutoringSession

#     now = timezone.now()
#     cutoff = now - timedelta(hours=2)  # 2h grace period after scheduled_at

#     noshow_sessions = TutoringSession.objects.filter(
#         status=TutoringSession.Status.CONFIRMED,
#         scheduled_at__lt=cutoff,
#         started_at__isnull=True,
#     )

#     updated_count = 0
#     for session in noshow_sessions:
#         session.status = TutoringSession.Status.CANCELED
#         session.save(update_fields=["status"])
#         # TODO: trigger refund task here → refund_session.delay(session.id)
#         updated_count += 1

#     return f"Canceled {updated_count} no-show sessions"
