import logging
import secrets

from django.db import transaction
from django.utils import timezone

from ..helpers import GoogleMeetError, cancel_meet_event, create_meet_event
from ..models import GoogleSession
from ..tasks.meet import (
    auto_complete_session,
    send_session_confirmed_emails,
    send_session_reminder,
)

logger = logging.getLogger(__name__)


class MeetService:

    @staticmethod
    @transaction.atomic
    def request_session(
        *, student, teacher, proposed_start, proposed_end, notes=""
    ) -> GoogleSession:
        """Student requests a session. Teacher must approve before payment."""
        from apps.billing.services import StripeService  # avoid circular import

        profile = teacher.teacher_profile
        price = profile.hour_price
        # platform_fee_percent = getattr(settings, "PLATFORM_FEE_PERCENT", 10)
        # platform_fee = (price * Decimal(platform_fee_percent)) / Decimal("100")
        # teacher_amount = price - platform_fee

        session = GoogleSession.objects.create(
            student=student,
            teacher=teacher,
            proposed_start=proposed_start,
            proposed_end=proposed_end,
            duration_minutes=int((proposed_end - proposed_start).total_seconds() / 60),
            price_amount=price,
            student_notes=notes,
        )
        # Notify teacher (async)
        from ..tasks.meet import notify_teacher_new_request

        notify_teacher_new_request.delay(session.pk)
        return session

    @staticmethod
    @transaction.atomic
    def teacher_accept(session: GoogleSession) -> GoogleSession:
        session.accept()
        session.save()
        # Notify student: "your session is approved, pay to confirm"
        from ..tasks.meet import notify_student_pending_payment

        notify_student_pending_payment.delay(session.pk)
        return session

    @staticmethod
    @transaction.atomic
    def teacher_reject(session: GoogleSession, reason: str = "") -> GoogleSession:
        session.reject(reason=reason)
        session.save()
        from ..tasks.meet import notify_student_rejected

        notify_student_rejected.delay(session.pk)
        return session

    @staticmethod
    @transaction.atomic
    def on_payment_confirmed(session: GoogleSession, payment) -> GoogleSession:
        """
        Called by billing webhook after Chargily confirms the payment.
        Transitions state, creates Google Meet event, schedules Celery tasks.
        """
        session.payment = payment
        session.mark_paid()
        session.save()

        # Generate join code (optional extra barrier)
        session.join_code = secrets.token_urlsafe(8)

        # Create Google Calendar event + Meet link
        try:
            result = create_meet_event(session)
            session.google_event_id = result["event_id"]
            session.google_meet_link = result["meet_link"]
            session.google_calendar_link = result["html_link"]
        except GoogleMeetError:
            logger.error(
                "Meet link generation failed for session %s, retrying async", session.pk
            )
            from ..tasks.meet import retry_create_meet_event

            retry_create_meet_event.apply_async(args=[session.pk], countdown=60)

        session.save()

        # Schedule reminders & auto-complete
        _schedule_session_tasks(session)

        return session

    @staticmethod
    @transaction.atomic
    def start_session(session: GoogleSession) -> GoogleSession:
        """Teacher explicitly launches the meeting."""
        session.start()
        session.save()
        return session

    @staticmethod
    @transaction.atomic
    def complete_session(session: GoogleSession) -> GoogleSession:
        session.complete()
        session.save()
        from apps.billing.services import EarningsService

        EarningsService.credit_teacher(session=session)
        from ..tasks.meet import request_student_review

        request_student_review.delay(session.pk)
        return session

    @staticmethod
    @transaction.atomic
    def cancel_session(
        session: GoogleSession, actor, reason: str = ""
    ) -> GoogleSession:
        session.cancel(reason=reason)
        session.save()
        if session.google_event_id:
            cancel_meet_event(session.google_event_id)
        # Trigger refund if student already paid
        if session.payment_id:
            from billing.services import RefundService

            RefundService.initiate_refund(session.payment)
        return session


def _schedule_session_tasks(session: GoogleSession):
    """Schedule all time-based tasks once a session is confirmed+paid."""
    now = timezone.now()
    start = session.confirmed_start

    # 1h before reminder
    eta_1h = start - timezone.timedelta(hours=1)
    if eta_1h > now:
        send_session_reminder.apply_async(
            args=[session.pk, "1h"],
            eta=eta_1h,
        )

    # 15 min before reminder
    eta_15m = start - timezone.timedelta(minutes=15)
    if eta_15m > now:
        send_session_reminder.apply_async(
            args=[session.pk, "15m"],
            eta=eta_15m,
        )

    # Auto-complete 15 minutes after expected end
    eta_complete = session.confirmed_end + timezone.timedelta(minutes=15)
    auto_complete_session.apply_async(
        args=[session.pk],
        eta=eta_complete,
    )
