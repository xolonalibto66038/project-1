from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from common.models import TimeStampModel

from .answer import Answer


class Attempt(TimeStampModel):
    """
    Records when a student takes a quiz - tracks progress, timing, and scoring
    """

    # Core relationships
    student = models.ForeignKey(
        "accounts.CustomUser",
        on_delete=models.CASCADE,
        related_name="attempts",
        limit_choices_to={"role": "student"},
    )
    quiz = models.ForeignKey(
        "Quiz", on_delete=models.CASCADE, related_name="quiz_attempts"
    )

    # Attempt tracking
    attempt_number = models.PositiveIntegerField(
        help_text=_("Which attempt this is for the student (1st, 2nd, etc.)")
    )

    # Timing information
    started_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=_("Started At"),
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    time_taken = models.DurationField(
        null=True, blank=True, help_text=_("Actual time taken to complete the quiz")
    )

    # Status tracking
    is_completed = models.BooleanField(
        default=False, help_text=_("Whether the attempt has been submitted")
    )

    is_timed_out = models.BooleanField(
        default=False,
        help_text=_("Whether the attempt was auto-submitted due to time limit"),
    )

    # Scoring
    total_points_possible = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        help_text=_("Total points possible at time of attempt"),
    )

    total_points_earned = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        help_text=_("Total points earned by the student"),
    )

    score_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text=_("Percentage score (0-100)"),
    )

    # Grading status
    is_graded = models.BooleanField(
        default=False, help_text=_("Whether all answers have been graded")
    )

    auto_graded_at = models.DateTimeField(
        null=True, blank=True, help_text=_("When auto-grading was completed")
    )

    manually_graded_at = models.DateTimeField(
        null=True, blank=True, help_text=_("When manual grading was completed")
    )

    graded_by = models.ForeignKey(
        "accounts.CustomUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="graded_attempts",
        help_text=_("Instructor who did manual grading"),
        limit_choices_to={"role": "teacher"},
    )

    # Additional information
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        editable=False,
        help_text=_("IP address from which attempt was made"),
    )

    user_agent = models.TextField(
        blank=True, editable=False, help_text=_("Browser/device information")
    )

    notes = models.TextField(
        blank=True, help_text=_("Additional notes about this attempt")
    )

    class Meta:
        db_table = "attempts"
        verbose_name = _("Attempt")
        verbose_name_plural = _("Attempts")
        ordering = ["-started_at", "-submitted_at"]
        unique_together = ["student", "quiz", "attempt_number"]
        indexes = [
            models.Index(fields=["student", "quiz"]),
            models.Index(fields=["started_at"]),
            models.Index(fields=["is_completed"]),
        ]

    def __str__(self):
        status = "Completed" if self.is_completed else "In Progress"
        return f"{self.student.get_full_name()} - {self.quiz.title} (Attempt #{self.attempt_number}) - {status}"

    def save(self, *args, **kwargs):
        """
        Ensure attempt_number is auto-incremented per (user, quiz)
        in a concurrency-safe way.
        """
        if not self.pk and not self.attempt_number:
            with transaction.atomic():
                last_attempt = (
                    Attempt.objects.select_for_update()
                    .filter(student=self.user, quiz=self.quiz)
                    .order_by("-attempt_number")
                    .first()
                )

                self.attempt_number = (
                    last_attempt.attempt_number + 1 if last_attempt else 1
                )
        # # Auto-set attempt number if not provided
        # if not self.attempt_number:
        #     last_attempt = (
        #         Attempt.objects.filter(student=self.student, quiz=self.quiz)
        #         .order_by("-attempt_number")
        #         .first()
        #     )

        #     self.attempt_number = (
        #         (last_attempt.attempt_number + 1) if last_attempt else 1
        #     )

        # Auto-set started_at if not provided (for new attempts)
        if not self.started_at and not self.pk:  # Only for new instances
            self.started_at = timezone.now()

        # Calculate time taken if being submitted
        if self.submitted_at and not self.time_taken:
            if self.started_at:
                self.time_taken = self.submitted_at - self.started_at
            else:
                # Handle case where started_at is somehow None
                raise ValidationError(
                    _("Cannot calculate time_taken: started_at is not set. "),
                    _("Ensure started_at is populated before submitting."),
                )

        # Validation: submitted_at should not be before started_at
        if (
            self.submitted_at
            and self.started_at
            and self.submitted_at < self.started_at
        ):
            raise ValidationError(_("submitted_at cannot be before started_at"))

        super().save(*args, **kwargs)

    def clean(self):
        """Additional model validation"""
        super().clean()

        # Ensure started_at is set if submitted_at is set
        if self.submitted_at and not self.started_at:
            raise ValidationError(
                {
                    "started_at": _(
                        "started_at must be set when submitted_at is provided"
                    )
                }
            )

        # Ensure submitted_at is not in the future
        # if self.submitted_at and self.submitted_at > timezone.now():
        #     raise ValidationError(
        #         {"submitted_at": _("submitted_at cannot be in the future")}
        #     )

    @property
    def is_passed(self):
        """Check if the attempt passed based on quiz passing score"""
        return self.score_percentage >= self.quiz.passing_score

    @property
    def time_remaining(self):
        """Get remaining time if quiz has time limit"""
        if not self.quiz.time_limit or self.is_completed:
            return None

        elapsed = timezone.now() - self.started_at
        time_limit = timezone.timedelta(minutes=self.quiz.time_limit)
        remaining = time_limit - elapsed

        return remaining if remaining.total_seconds() > 0 else timezone.timedelta(0)

    @property
    def is_expired(self):
        """Check if attempt has exceeded time limit"""
        if not self.quiz.time_limit or self.is_completed:
            return False

        elapsed = timezone.now() - self.started_at
        time_limit = timezone.timedelta(minutes=self.quiz.time_limit)
        return elapsed > time_limit

    def submit(self, auto_submit=False):
        """Submit the attempt and calculate scores"""
        if self.is_completed:
            return False, "Attempt already submitted"

        with transaction.atomic():
            self.submitted_at = timezone.now()
            self.is_completed = True
            self.is_timed_out = auto_submit

            self.calculate_score()
            self.save()

        return True, "Attempt submitted successfully"

    # def calculate_score(self):
    #     """Calculate the total score for this attempt"""
    #     from django.db.models import Sum

    #     # Get all answers for this attempt
    #     # answers = Answer.objects.filter(
    #     #     user=self.user,
    #     #     question_content_type__in=self.quiz.quiz_questions.values_list(
    #     #         "question_content_type", flat=True
    #     #     ),
    #     #     question_object_id__in=self.quiz.quiz_questions.values_list(
    #     #         "question_object_id", flat=True
    #     #     ),
    #     # )
    #     answers = self.answers.all()

    #     # Calculate totals
    #     self.total_points_possible = self.quiz.total_points
    #     self.total_points_earned = (
    #         answers.aggregate(total=Sum("points_earned"))["total"] or 0
    #     )

    #     # Calculate percentage
    #     if self.total_points_possible > 0:
    #         self.score_percentage = (
    #             (self.total_points_earned / self.total_points_possible) * Decimal("100")
    #         ).quantize(Decimal("0.01"))
    #     else:
    #         self.score_percentage = 0

    #     # Check if fully graded
    #     total_answers_needed = self.quiz.question_count
    #     graded_answers = answers.filter(is_correct__isnull=False).count()
    #     self.is_graded = graded_answers >= total_answers_needed
    def calculate_score(self):
        from django.db.models import Sum

        answers = self.answers.all()

        self.total_points_possible = Decimal(self.quiz.total_points)

        total = answers.aggregate(total=Sum("points_earned"))["total"]

        # Ensure Decimal
        self.total_points_earned = total if total is not None else Decimal("0.00")

        if self.total_points_possible > 0:
            self.score_percentage = (
                (self.total_points_earned / self.total_points_possible) * Decimal("100")
            ).quantize(Decimal("0.01"))
        else:
            self.score_percentage = Decimal("0.00")

        total_answers_needed = self.quiz.question_count
        graded_answers = answers.filter(is_correct__isnull=False).count()
        self.is_graded = graded_answers >= total_answers_needed

    def get_answers(self):
        """Get all answers for this attempt"""
        quiz_questions = self.quiz.quiz_questions.all()
        question_ids = [
            (qq.question_content_type_id, qq.question_object_id)
            for qq in quiz_questions
        ]

        answers = Answer.objects.filter(
            student=self.student,
            question_content_type_id__in=[qid[0] for qid in question_ids],
            question_object_id__in=[qid[1] for qid in question_ids],
        )

        return answers

    def get_grade_letter(self):
        """Get letter grade based on percentage"""
        if self.score_percentage >= 90:
            return "A"
        elif self.score_percentage >= 80:
            return "B"
        elif self.score_percentage >= 70:
            return "C"
        elif self.score_percentage >= 60:
            return "D"
        else:
            return "F"
