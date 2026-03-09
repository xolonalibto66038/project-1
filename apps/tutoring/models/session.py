# apps/tutoring/models.py

from django.conf import settings
from django.db import models

from common.models import TimeStampModel


class TutoringSession(TimeStampModel):

    class Status(models.TextChoices):

        PENDING_PAYMENT = "pending_payment"

        PAYMENT_AUTHORIZED = "payment_authorized"

        CONFIRMED = "confirmed"

        IN_PROGRESS = "in_progress"

        COMPLETED = "completed"

        PAYMENT_FAILED = "payment_failed"

        CANCELED = "canceled"

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student_sessions",
        limit_choices_to={"role": "student"},
    )

    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="teacher_sessions",
        limit_choices_to={"role": "teacher"},
    )

    price = models.DecimalField(max_digits=8, decimal_places=2)

    platform_fee = models.DecimalField(max_digits=8, decimal_places=2)

    teacher_amount = models.DecimalField(max_digits=8, decimal_places=2)

    status = models.CharField(max_length=32, choices=Status.choices)

    # Payment binding
    stripe_checkout_session_id = models.CharField(
        max_length=255, unique=True, null=True
    )

    stripe_payment_intent_id = models.CharField(max_length=255, unique=True, null=True)

    stripe_transfer_id = models.CharField(max_length=255, null=True)

    payment_authorized_at = models.DateTimeField(null=True)

    # Scheduling
    scheduled_at = models.DateTimeField(null=True)

    duration_minutes = models.PositiveIntegerField(default=60)

    confirmed_at = models.DateTimeField(null=True)

    # Zoom
    zoom_meeting_id = models.CharField(max_length=255, null=True)
    zoom_join_url = models.URLField(null=True)
    zoom_start_url = models.URLField(null=True)

    # Meet
    meeting_id        = models.CharField(max_length=255, null=True)
    meeting_join_url  = models.URLField(null=True)
    meeting_start_url = models.URLField(null=True)
    meeting_event_id  = models.CharField(max_length=255, null=True) 

    # Completion
    started_at = models.DateTimeField(null=True)

    completed_at = models.DateTimeField(null=True)

    teacher_paid = models.BooleanField(default=False)

    teacher_paid_at = models.DateTimeField(null=True)
