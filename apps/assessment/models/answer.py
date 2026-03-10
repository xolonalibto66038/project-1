from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import TimeStampModel


class Answer(TimeStampModel):
    """
    Stores user answers to any type of question
    Uses Generic Foreign Key to work with different question types
    """

    # Link to user who provided the answer
    student = models.ForeignKey(
        "accounts.CustomUser",
        on_delete=models.CASCADE,
        related_name="answers",
        limit_choices_to={"role": "student"},
    )

    attempt = models.ForeignKey(
        "Attempt",
        on_delete=models.CASCADE,
        related_name="answers",
    )

    selected_choices = models.ManyToManyField(
        "Choice",
        blank=True,
        related_name="answers",
    )

    # Generic relationship to any question type (TextQuestion, MultipleChoiceQuestion, etc.)
    question_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    question_object_id = models.UUIDField(
        verbose_name=_("Object ID"), help_text=_("ID of the question being answered")
    )
    question = GenericForeignKey("question_content_type", "question_object_id")

    # The actual answer content
    answer_text = models.TextField(
        blank=True,
        help_text=_(
            _("Text answer for text questions or selected choice for multiple choice")
        ),
    )

    # For questions that might have boolean answers (True/False)
    answer_boolean = models.BooleanField(
        null=True, blank=True, help_text=_("Boolean answer for True/False questions")
    )

    # Grading information
    points_earned = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text=_("Points earned for this answer"),
    )

    is_correct = models.BooleanField(
        null=True,
        blank=True,
        help_text=_("Whether the answer is correct (null if not graded yet)"),
    )

    # Instructor feedback
    feedback = models.TextField(
        blank=True, help_text=_("Instructor feedback on the answer")
    )

    # Metadata
    submitted_at = models.DateTimeField(auto_now_add=True)
    graded_at = models.DateTimeField(null=True, blank=True)
    graded_by = models.ForeignKey(
        "accounts.CustomUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="graded_answers",
        limit_choices_to={"role": "teacher"},
    )

    class Meta:
        db_table = "answers"
        ordering = ["-submitted_at"]
        verbose_name = _("Answer")
        verbose_name_plural = _("Answers")
        # Ensure one answer per user per question
        unique_together = [
            "student",
            "attempt",
            "question_content_type",
            "question_object_id",
        ]

        indexes = [
            models.Index(fields=["attempt"]),
            models.Index(fields=["student"]),
        ]

    def __str__(self):
        username = getattr(self.student, "username", "Unknown")
        return f"{username}'s answer to {self.question}"

    # def clean(self):
    #     super().clean()

    #     filled_fields = sum(
    #         [
    #             bool(self.answer_text),
    #             self.answer_boolean is not None,
    #             self.selected_choices.exists() if self.pk else False,
    #         ]
    #     )

    #     if filled_fields > 1:
    #         raise ValidationError("Only one type of answer can be provided.")
    def clean(self):
        super().clean()

        # ── Check mutually exclusive answer types ──
        # M2M (selected_choices) is checked separately via post-save signal
        # Here we only validate the non-M2M fields
        non_m2m_filled = sum(
            [
                bool(self.answer_text),
                self.answer_boolean is not None,
            ]
        )

        if non_m2m_filled > 1:
            raise ValidationError(
                _("Only one type of answer can be provided at a time.")
            )

        # ── For existing instances, also check M2M doesn't conflict ──
        if self.pk:
            has_choices = self.selected_choices.exists()
            if has_choices and non_m2m_filled > 0:
                raise ValidationError(
                    _("Cannot combine selected choices with text or boolean answer.")
                )

        # ── Validate points_earned is not negative ──
        if self.points_earned is not None and self.points_earned < 0:
            raise ValidationError(_("Points earned cannot be negative."))

        # ── Validate grading consistency ──
        if self.graded_at and not self.graded_by and self.is_correct is None:
            raise ValidationError(_("A graded answer must have is_correct set."))

    @property
    def is_graded(self):
        """Check if the answer has been graded"""
        return self.is_correct is not None

    @property
    def answer_preview(self):
        """Get a short preview of the answer"""
        if self.answer_text:
            return (
                self.answer_text[:50] + "..."
                if len(self.answer_text) > 50
                else self.answer_text
            )
        elif self.answer_boolean is not None:
            return "True" if self.answer_boolean else "False"
        return "No answer"

    def get_answer_value(self):
        """Get the actual answer value regardless of type"""
        if self.answer_text:
            return self.answer_text
        elif self.answer_boolean is not None:
            return self.answer_boolean
        return None

    def mark_as_correct(self, points=None, graded_by=None):
        """Mark answer as correct and assign points"""
        from django.utils import timezone

        self.is_correct = True
        self.points_earned = points or self.question.points
        self.graded_at = timezone.now()
        if graded_by:
            self.graded_by = graded_by
        self.save()

    def mark_as_incorrect(self, points=0, graded_by=None):
        """Mark answer as incorrect"""
        from django.utils import timezone

        self.is_correct = False
        self.points_earned = points
        self.graded_at = timezone.now()
        if graded_by:
            self.graded_by = graded_by
        self.save()

    def auto_grade(self):
        """
        Automatically grade the answer if supported by the question type.
        """
        if self.attempt.is_completed:
            return

        q = self.question

        if q.question_type == "tf":
            self.is_correct = self.answer_boolean == q.correct_answer

        elif q.question_type == "mcq":
            correct_ids = set(q.correct_choices.values_list("id", flat=True))
            selected_ids = set(self.selected_choices.values_list("id", flat=True))
            self.is_correct = correct_ids == selected_ids

        else:
            # Text / essay questions cannot be auto-graded safely
            self.is_correct = None
            return

        if self.is_correct:
            self.points_earned = q.points
        else:
            self.points_earned = 0

        self.save(update_fields=["is_correct", "points_earned", "updated_at"])
