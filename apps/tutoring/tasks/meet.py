import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def notify_teacher_new_request(self, session_pk: int):
    from ..models import GoogleSession

    try:
        session = GoogleSession.objects.select_related("student", "teacher").get(
            pk=session_pk
        )
        send_mail(
            subject=f"New tutoring request from {session.student.get_full_name()}",
            message=(
                f"Hi {session.teacher.first_name},\n\n"
                f"{session.student.get_full_name()} has requested a session on "
                f"{session.proposed_start.strftime('%A %d %B %Y at %H:%M')}.\n\n"
                f"Log in to review and accept or decline."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[session.teacher.email],
        )
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def notify_student_pending_payment(self, session_pk: int):
    from ..models import GoogleSession

    try:
        session = GoogleSession.objects.select_related("student", "teacher").get(
            pk=session_pk
        )
        pay_url = f"{settings.FRONTEND_BASE_URL}/sessions/{session.pk}/pay/"
        send_mail(
            subject="Your session has been approved — complete your payment",
            message=(
                f"Hi {session.student.first_name},\n\n"
                f"{session.teacher.get_full_name()} has accepted your session request.\n"
                f"Complete your payment here to confirm: {pay_url}\n\n"
                f"Amount due: {session.price_amount} {session.price_currency}"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[session.student.email],
        )
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=5, default_retry_delay=300)
def retry_create_meet_event(self, session_pk: int):
    """Fallback if Meet link generation failed during webhook processing."""
    from ..helpers import GoogleMeetError, create_meet_event
    from ..models import GoogleSession

    try:
        session = GoogleSession.objects.get(pk=session_pk)
        if session.google_meet_link:
            return  # already fixed
        result = create_meet_event(session)
        session.google_event_id = result["event_id"]
        session.google_meet_link = result["meet_link"]
        session.google_calendar_link = result["html_link"]
        session.save(
            update_fields=[
                "google_event_id",
                "google_meet_link",
                "google_calendar_link",
            ]
        )
        # Now send the confirmation email
        send_session_confirmed_emails.delay(session_pk)
    except GoogleMeetError as exc:
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3)
def send_session_confirmed_emails(self, session_pk: int):
    from ..models import GoogleSession

    try:
        session = GoogleSession.objects.select_related("student", "teacher").get(
            pk=session_pk
        )
        body = (
            f"Your session is confirmed!\n\n"
            f"Date: {session.confirmed_start.strftime('%A %d %B %Y')}\n"
            f"Time: {session.confirmed_start.strftime('%H:%M')} — {session.confirmed_end.strftime('%H:%M')}\n"
            f"Google Meet: {session.google_meet_link}\n"
            f"Join code: {session.join_code}\n\n"
            f"Add to Google Calendar: {session.google_calendar_link}"
        )
        for recipient in [session.student, session.teacher]:
            send_mail(
                subject="Session confirmed — Google Meet link inside",
                message=f"Hi {recipient.first_name},\n\n{body}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient.email],
            )
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3)
def send_session_reminder(self, session_pk: int, window: str):
    from ..models import GoogleSession

    try:
        session = GoogleSession.objects.select_related("student", "teacher").get(
            pk=session_pk
        )
        if session.state not in (
            GoogleSession.State.PAID,
            GoogleSession.State.ACTIVE,
        ):
            return  # cancelled in the meantime
        label = "1 hour" if window == "1h" else "15 minutes"
        for recipient in [session.student, session.teacher]:
            send_mail(
                subject=f"Your session starts in {label}",
                message=(
                    f"Hi {recipient.first_name},\n\n"
                    f"Reminder: your tutoring session starts in {label}.\n"
                    f"Join here: {session.google_meet_link}"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient.email],
            )
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3)
def auto_complete_session(self, session_pk: int):
    """Automatically marks a session as completed 15 min after expected end."""
    from ..models import GoogleSession
    from ..services.meet import MeetService

    try:
        session = GoogleSession.objects.get(pk=session_pk)
        if session.state == GoogleSession.State.ACTIVE:
            MeetService.complete_session(session)
        elif session.state == GoogleSession.State.PAID:
            # Teacher never launched but time is up — still complete
            session.start()
            session.save()
            MeetService.complete_session(session)
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task
def notify_student_rejected(session_pk: int):
    from ..models import GoogleSession

    session = GoogleSession.objects.select_related("student", "teacher").get(
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
def request_student_review(session_pk: int):
    from ..models import GoogleSession

    session = GoogleSession.objects.select_related("student", "teacher").get(
        pk=session_pk
    )
    review_url = f"{settings.FRONTEND_BASE_URL}/sessions/{session.pk}/review/"
    send_mail(
        subject=f"How was your session with {session.teacher.get_full_name()}?",
        message=(
            f"Hi {session.student.first_name},\n\n"
            f"Leave a review for your session: {review_url}"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[session.student.email],
    )
