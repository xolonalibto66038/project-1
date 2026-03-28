# apps/tutoring/models.py

from django.conf import settings
from django.db import models
from django_fsm import FSMField, transition

from common.models import TimeStampModel


class ZoomSession(TimeStampModel):
    """
    Lifecycle:
      pending_teacher → pending_payment → payment_authorized → confirmed → in_progress → completed
                      ↘ cancelled        ↘ payment_failed       ↘ cancelled
    """

    class State(models.TextChoices):
        PENDING_TEACHER = "pending_teacher", "Pending Teacher Approval"
        PENDING_PAYMENT = "pending_payment", "Pending Payment"
        PAYMENT_AUTHORIZED = "payment_authorized", "Payment Authorized"
        PAYMENT_FAILED = "payment_failed", "Payment Failed"
        CONFIRMED = "confirmed", "Confirmed"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"
        CANCELED = "canceled", "Canceled"

    # ── Participants ───────────────────────────────────────────────────
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="student_sessions",
        limit_choices_to={"role": "student"},
    )
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="teacher_sessions",
        limit_choices_to={"role": "teacher"},
    )

    # ── Scheduling ─────────────────────────────────────────────────────
    proposed_start = models.DateTimeField()
    proposed_end = models.DateTimeField()
    confirmed_start = models.DateTimeField(null=True, blank=True)
    confirmed_end = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(default=60)

    # ── Pricing ────────────────────────────────────────────────────────
    price = models.DecimalField(max_digits=10, decimal_places=2)
    # platform_fee = models.DecimalField(max_digits=10, decimal_places=2)
    # teacher_amount = models.DecimalField(max_digits=10, decimal_places=2)
    price_currency = models.CharField(max_length=3, default="DZD")

    # ── FSM state ──────────────────────────────────────────────────────
    state = FSMField(default=State.PENDING_TEACHER, protected=True)

    # ── Stripe ─────────────────────────────────────────────────────────
    stripe_checkout_session_id = models.CharField(
        max_length=255, unique=True, null=True, blank=True
    )
    stripe_payment_intent_id = models.CharField(
        max_length=255, unique=True, null=True, blank=True
    )
    stripe_transfer_id = models.CharField(max_length=255, null=True, blank=True)
    payment_authorized_at = models.DateTimeField(null=True, blank=True)

    # ── Zoom ───────────────────────────────────────────────────────────
    zoom_meeting_id = models.CharField(max_length=255, null=True, blank=True)
    zoom_join_url = models.URLField(null=True, blank=True)
    zoom_start_url = models.URLField(null=True, blank=True)
    zoom_password = models.CharField(max_length=64, null=True, blank=True)

    # ── Completion & payout ────────────────────────────────────────────
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    teacher_paid = models.BooleanField(default=False)
    teacher_paid_at = models.DateTimeField(null=True, blank=True)

    # ── Notes & cancellation ───────────────────────────────────────────
    teacher_notes = models.TextField(blank=True)
    student_notes = models.TextField(blank=True)
    cancellation_reason = models.TextField(blank=True)
    canceled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="canceled_sessions",
    )

    # ── FSM transitions ────────────────────────────────────────────────

    @transition(field=state, source=State.PENDING_TEACHER, target=State.PENDING_PAYMENT)
    def accept(self):
        """Teacher approves the session request."""
        self.confirmed_start = self.proposed_start
        self.confirmed_end = self.proposed_end

    @transition(field=state, source=State.PENDING_TEACHER, target=State.CANCELED)
    def reject(self, reason="", canceled_by=None):
        """Teacher rejects the session request before payment."""
        self.cancellation_reason = reason
        self.canceled_by = canceled_by

    @transition(
        field=state, source=State.PENDING_PAYMENT, target=State.PAYMENT_AUTHORIZED
    )
    def authorize_payment(self, payment_intent_id=None):
        """Stripe webhook confirms payment intent authorized."""
        from django.utils import timezone

        self.payment_authorized_at = timezone.now()
        if payment_intent_id:
            self.stripe_payment_intent_id = payment_intent_id

    @transition(field=state, source=State.PENDING_PAYMENT, target=State.PAYMENT_FAILED)
    def fail_payment(self):
        """Stripe webhook reports payment failure."""
        pass

    @transition(field=state, source=State.PAYMENT_AUTHORIZED, target=State.CONFIRMED)
    def confirm(
        self,
        zoom_meeting_id=None,
        zoom_join_url=None,
        zoom_start_url=None,
        zoom_password=None,
    ):
        """
        Payment captured — provision Zoom meeting and mark confirmed.
        Caller is responsible for creating the Zoom meeting beforehand
        and passing the details in.
        """
        from django.utils import timezone

        self.zoom_meeting_id = zoom_meeting_id
        self.zoom_join_url = zoom_join_url
        self.zoom_start_url = zoom_start_url
        self.zoom_password = zoom_password

    @transition(field=state, source=State.CONFIRMED, target=State.IN_PROGRESS)
    def start(self):
        """Session has begun."""
        from django.utils import timezone

        self.started_at = timezone.now()

    @transition(field=state, source=State.IN_PROGRESS, target=State.COMPLETED)
    def complete(self):
        """Session ended successfully."""
        from django.utils import timezone

        self.completed_at = timezone.now()

    @transition(
        field=state,
        source=[State.PENDING_TEACHER, State.PENDING_PAYMENT, State.CONFIRMED],
        target=State.CANCELED,
    )
    def cancel(self, reason="", canceled_by=None):
        """Cancel from any pre-active state."""
        self.cancellation_reason = reason
        self.canceled_by = canceled_by

    # ── Helpers ────────────────────────────────────────────────────────

    @property
    def is_zoom_ready(self) -> bool:
        return bool(self.zoom_meeting_id and self.zoom_join_url)

    def __str__(self):
        return (
            f"Session {self.pk}: {self.student} → {self.teacher} "
            f"@ {self.confirmed_start or self.proposed_start} [{self.state}]"
        )

    class Meta:
        ordering = ["-created_at"]
