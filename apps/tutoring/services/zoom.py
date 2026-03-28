# apps/tutoring/services/zoom_service.py

import logging

from django.db import transaction
from django.utils import timezone

from ..helpers import ZoomError, cancel_zoom_meeting, create_zoom_meeting
from ..models import ZoomSession
from ..tasks.zoom import (
    auto_complete_session,
    notify_student_payment_failed,
    notify_student_pending_payment,
    notify_student_rejected,
    notify_teacher_new_request,
    request_student_review,
    retry_create_zoom_meeting,
    send_session_reminder,
)

logger = logging.getLogger(__name__)


class ZoomService:

    @staticmethod
    @transaction.atomic
    def request_session(
        *, student, teacher, proposed_start, proposed_end, notes=""
    ) -> ZoomSession:
        """Student requests a session. Teacher must approve before payment."""
        profile = teacher.teacher_profile
        price = profile.hour_price

        session = ZoomSession.objects.create(
            student=student,
            teacher=teacher,
            proposed_start=proposed_start,
            proposed_end=proposed_end,
            duration_minutes=int((proposed_end - proposed_start).total_seconds() / 60),
            price=price,
            student_notes=notes,
        )

        notify_teacher_new_request.delay(session.pk)
        return session

    @staticmethod
    @transaction.atomic
    def teacher_accept(session: ZoomSession) -> ZoomSession:
        """Teacher approves the session — student is notified to pay."""
        session.accept()
        session.save()

        notify_student_pending_payment.delay(session.pk)
        return session

    @staticmethod
    @transaction.atomic
    def teacher_reject(session: ZoomSession, reason: str = "") -> ZoomSession:
        """Teacher declines the session request."""
        session.reject(reason=reason)
        session.save()

        notify_student_rejected.delay(session.pk)
        return session

    @staticmethod
    @transaction.atomic
    def on_payment_authorized(
        session: ZoomSession,
        payment_intent_id: str,
    ) -> ZoomSession:
        """
        Called by Stripe webhook after payment_intent.amount_capturable_updated
        (authorize & capture flow) or payment_intent.succeeded.

        Transitions to PAYMENT_AUTHORIZED, provisions a Zoom meeting,
        then transitions to CONFIRMED.
        """
        session.authorize_payment(payment_intent_id=payment_intent_id)
        session.save()

        # Create Zoom meeting
        zoom_data = None
        try:
            zoom_data = create_zoom_meeting(session)
        except ZoomError:
            logger.error(
                "Zoom meeting creation failed for session %s, retrying async",
                session.pk,
            )
            retry_create_zoom_meeting.apply_async(args=[session.pk], countdown=60)

        # Transition to CONFIRMED (with or without Zoom data — retry task
        # will call confirm() again once the meeting is created)
        if zoom_data:
            session.confirm(
                zoom_meeting_id=zoom_data["meeting_id"],
                zoom_join_url=zoom_data["join_url"],
                zoom_start_url=zoom_data["start_url"],
                zoom_password=zoom_data.get("password"),
            )
            session.save()

            _schedule_session_tasks(session)

        return session

    @staticmethod
    @transaction.atomic
    def on_payment_failed(session: ZoomSession) -> ZoomSession:
        """Called by Stripe webhook on payment_intent.payment_failed."""
        session.fail_payment()
        session.save()

        from ..tasks.zoom import notify_student_payment_failed

        notify_student_payment_failed.delay(session.pk)
        return session

    @staticmethod
    @transaction.atomic
    def start_session(session: ZoomSession) -> ZoomSession:
        """Teacher explicitly launches the Zoom meeting."""
        session.start()
        session.save()
        return session

    @staticmethod
    @transaction.atomic
    def complete_session(session: ZoomSession) -> ZoomSession:
        """Mark session completed and credit the teacher."""
        session.complete()
        session.save()

        from apps.billing.services import EarningsService

        EarningsService.credit_teacher(session=session)

        request_student_review.delay(session.pk)
        return session

    @staticmethod
    @transaction.atomic
    def cancel_session(session: ZoomSession, actor, reason: str = "") -> ZoomSession:
        """
        Cancel the session, delete the Zoom meeting if one exists,
        and trigger a refund if payment was already authorized.
        """
        session.cancel(reason=reason, canceled_by=actor)
        session.save()

        if session.zoom_meeting_id:
            try:
                cancel_zoom_meeting(session.zoom_meeting_id)
            except ZoomError:
                logger.warning(
                    "Failed to delete Zoom meeting %s for session %s",
                    session.zoom_meeting_id,
                    session.pk,
                )

        # Refund if Stripe payment was already authorized
        if session.stripe_payment_intent_id:
            from apps.billing.services import RefundService

            RefundService.initiate_refund(session)

        return session


# ── Helpers ────────────────────────────────────────────────────────────────────


def _schedule_session_tasks(session: ZoomSession):
    """Schedule all time-based Celery tasks once a session is confirmed."""
    now = timezone.now()
    start = session.confirmed_start

    # 1 hour before reminder
    eta_1h = start - timezone.timedelta(hours=1)
    if eta_1h > now:
        send_session_reminder.apply_async(
            args=[session.pk, "1h"],
            eta=eta_1h,
        )

    # 15 minutes before reminder
    eta_15m = start - timezone.timedelta(minutes=15)
    if eta_15m > now:
        send_session_reminder.apply_async(
            args=[session.pk, "15m"],
            eta=eta_15m,
        )

    # Auto-complete 15 minutes after the session is expected to end
    eta_complete = session.confirmed_end + timezone.timedelta(minutes=15)
    auto_complete_session.apply_async(
        args=[session.pk],
        eta=eta_complete,
    )


# import base64

# import requests
# from django.conf import settings


# class ZoomService:

#     @staticmethod
#     def get_access_token():

#         url = "https://zoom.us/oauth/token"

#         credentials = f"{settings.ZOOM_CLIENT_ID}:{settings.ZOOM_CLIENT_SECRET}"
#         credentials_base64 = base64.b64encode(credentials.encode()).decode()

#         headers = {
#             "Authorization": f"Basic {credentials_base64}",
#             "Content-Type": "application/x-www-form-urlencoded",
#         }

#         params = {
#             "grant_type": "account_credentials",
#             "account_id": settings.ZOOM_ACCOUNT_ID,
#         }

#         response = requests.post(url, headers=headers, params=params)

#         return response.json()["access_token"]

#     @staticmethod
#     def create_meeting(session):

#         token = ZoomService.get_access_token()

#         response = requests.post(
#             url=f"{settings.ZOOM_BASE_URL}/users/{settings.ZOOM_HOST_EMAIL}/meetings",
#             headers={"Authorization": f"Bearer {token}"},
#             json={
#                 "topic": f"Tutoring session {session.id}",
#                 "type": 2,
#                 "start_time": session.scheduled_at.isoformat(),
#                 "duration": session.duration_minutes,
#                 "settings": {
#                     "waiting_room": True,
#                     "join_before_host": False,
#                     "meeting_authentication": False,
#                     "password": "",
#                     "passcode": "",
#                     "auto_recording": "none",
#                     "use_pmi": False,
#                     "enforce_login": False,
#                 },
#                 # "settings": {"waiting_room": True, "join_before_host": False, "password_required": False, "use_pmi": False,},
#             },
#             timeout=10,
#         )

#         response.raise_for_status()

#         return response.json()

#     @staticmethod
#     def disable_passcode_requirement():
#         """
#         Run this once to disable passcode at account level.
#         Zoom account settings override per-meeting settings.
#         """
#         token = ZoomService.get_access_token()

#         requests.patch(
#             url=f"{settings.ZOOM_BASE_URL}/accounts/me/settings",
#             headers={"Authorization": f"Bearer {token}"},
#             json={
#                 "security": {
#                     "meeting_password": False,
#                     "require_password_for_all": False,
#                 }
#             },
#             timeout=10,
#         )
