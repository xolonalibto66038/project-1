from django.conf import settings
from django.db import models
from django.utils import timezone
from django_fsm import FSMField, transition


class GoogleSession(models.Model):
    """
    Lifecycle: pending_teacher → pending_payment → paid → active → completed
                                                         ↘ cancelled / refunded
    """

    class State(models.TextChoices):
        PENDING_TEACHER = "pending_teacher", "Pending Teacher Approval"
        PENDING_PAYMENT = "pending_payment", "Pending Payment"
        PAID = "paid", "Paid"
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"
        REFUNDED = "refunded", "Refunded"

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="tutoring_sessions_as_student",
        on_delete=models.PROTECT,
    )
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="tutoring_sessions_as_teacher",
        on_delete=models.PROTECT,
    )

    # Scheduling
    proposed_start = models.DateTimeField()
    proposed_end = models.DateTimeField()
    confirmed_start = models.DateTimeField(null=True, blank=True)
    confirmed_end = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(default=60)

    # Pricing
    price_amount = models.DecimalField(max_digits=10, decimal_places=2)
    price_currency = models.CharField(max_length=3, default="DZD")

    # FSM state
    state = FSMField(default=State.PENDING_TEACHER, protected=True)

    # Google Meet
    google_event_id = models.CharField(max_length=255, blank=True)
    google_meet_link = models.URLField(blank=True)
    google_calendar_link = models.URLField(blank=True)  # "add to calendar" link
    max_participants = models.PositiveIntegerField(
        default=settings.GOOGLE_MEET_MAX_PARTICIPANTS
    )
    join_code = models.CharField(max_length=16, blank=True)  # optional extra gate

    # Billing reference (FK to your Payment model)
    # payment = models.OneToOneField(
    #     "billing.Payment",
    #     null=True,
    #     blank=True,
    #     on_delete=models.SET_NULL,
    #     related_name="tutoring_session",
    # )

    # Metadata
    teacher_notes = models.TextField(blank=True)
    student_notes = models.TextField(blank=True)
    cancellation_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ── FSM transitions ────────────────────────────────────────────────
    @transition(field=state, source=State.PENDING_TEACHER, target=State.PENDING_PAYMENT)
    def accept(self):
        self.confirmed_start = self.proposed_start
        self.confirmed_end = self.proposed_end

    @transition(field=state, source=State.PENDING_TEACHER, target=State.CANCELLED)
    def reject(self, reason=""):
        self.cancellation_reason = reason

    @transition(field=state, source=State.PENDING_PAYMENT, target=State.PAID)
    def mark_paid(self):
        """Called by billing webhook after Chargily confirms payment."""
        pass

    @transition(field=state, source=State.PAID, target=State.ACTIVE)
    def start(self):
        pass

    @transition(field=state, source=State.ACTIVE, target=State.COMPLETED)
    def complete(self):
        pass

    @transition(
        field=state,
        source=[State.PENDING_TEACHER, State.PENDING_PAYMENT],
        target=State.CANCELLED,
    )
    def cancel(self, reason=""):
        self.cancellation_reason = reason

    @transition(field=state, source=State.PAID, target=State.REFUNDED)
    def refund(self):
        pass

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Session {self.pk}: {self.student} → {self.teacher} @ {self.confirmed_start}"
