# apps/assessment/models/mcq.py

from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import TimeStampModel

from .question import BaseQuestion


class MultipleChoiceQuestion(BaseQuestion):
    allow_multiple = models.BooleanField(
        default=False,
        verbose_name=_("Allow Multiple"),
        help_text=_("Whether students can select more than one correct answer."),
    )
    explanation = models.TextField(
        blank=True,
        verbose_name=_("Explanation"),
        help_text=_("Shown to the student after answering."),
    )

    class Meta:
        db_table = "mcq_questions"
        verbose_name = _("Multiple Choice Question")
        verbose_name_plural = _("Multiple Choice Questions")
        indexes = [
            models.Index(fields=["question_type"]),
            models.Index(fields=["difficulty_level"]),
            models.Index(fields=["is_active"]),
        ]

    def save(self, *args, **kwargs):
        self.question_type = "mcq"
        super().save(*args, **kwargs)

    def clean(self):
        """
        Only validate fields that exist at clean() time.
        Choice-related validation happens in post_save signal
        because choices are saved AFTER the question.
        """
        super().clean()
        # Nothing to validate here without choices —
        # allow_multiple consistency checked in signal

    def validate_choices(self):
        """
        Called explicitly from signal after choices are saved.
        Can also be called from admin or service layer.
        """
        from django.core.exceptions import ValidationError

        correct_count = self.choices.filter(is_correct=True).count()
        total_count = self.choices.count()

        if total_count < 2:
            raise ValidationError(
                _("A multiple choice question must have at least 2 choices.")
            )

        if correct_count == 0:
            raise ValidationError(_("At least one correct choice is required."))

        if not self.allow_multiple and correct_count > 1:
            raise ValidationError(
                _("Only one correct choice is allowed when allow_multiple is False.")
            )

    @property
    def correct_choices(self):
        return self.choices.filter(is_correct=True)

    def get_question_type(self):
        return "multiple_choice_question"  # ou une autre logique

    def grade(self, answer):
        if not isinstance(answer, list):
            return {
                "awarded_points": 0,
                "is_correct": False,
                "feedback": _("Invalid answer format."),
            }

        valid_choice_ids = set(self.choices.values_list("id", flat=True))
        submitted_ids = set(answer)

        if not submitted_ids.issubset(valid_choice_ids):
            return {
                "awarded_points": 0,
                "is_correct": False,
                "feedback": _("Invalid choice selection."),
            }

        correct_ids = set(self.correct_choices.values_list("id", flat=True))
        is_correct = submitted_ids == correct_ids
        awarded = self.points if is_correct else 0

        return {
            "awarded_points": awarded,
            "is_correct": is_correct,
            "feedback": self.explanation or "",
        }


# class MultipleChoiceQuestion(BaseQuestion):
#     allow_multiple = models.BooleanField(default=False)
#     explanation = models.TextField(blank=True)

#     class Meta:
#         db_table = "mcq_questions"
#         verbose_name = _("MCQ Question")
#         verbose_name_plural = _("MCQ Questions")
#         indexes = [
#             models.Index(fields=["question_type"]),
#             models.Index(fields=["difficulty_level"]),
#             models.Index(fields=["is_active"]),
#             models.Index(fields=["created_by"]),
#         ]

#     def save(self, *args, **kwargs):
#         self.question_type = "mcq"
#         super().save(*args, **kwargs)

#     @property
#     def correct_choices(self):
#         return self.choices.filter(is_correct=True)

#     def clean(self):
#         pass
#         # correct_count = self.choices.filter(is_correct=True).count()

#         # if correct_count == 0:
#         #     raise ValidationError("At least one correct choice is required.")

#         # if not self.allow_multiple and correct_count > 1:
#         #     raise ValidationError(
#         #         "Only one correct choice allowed when allow_multiple=False."
#         #     )

#     def get_question_type(self):
#         return "multiple_choice_question"  # ou une autre logique

#     def grade(self, answer):
#         if not isinstance(answer, list):
#             return {
#                 "awarded_points": 0,
#                 "is_correct": False,
#                 "feedback": "Invalid answer format.",
#             }

#         valid_choice_ids = set(self.choices.values_list("id", flat=True))

#         submitted_ids = set(answer)

#         # Security check: ensure choices belong to question
#         if not submitted_ids.issubset(valid_choice_ids):
#             return {
#                 "awarded_points": 0,
#                 "is_correct": False,
#                 "feedback": "Invalid choice selection.",
#             }

#         correct_ids = set(
#             self.choices.filter(is_correct=True).values_list("id", flat=True)
#         )

#         is_correct = submitted_ids == correct_ids
#         awarded = self.points if is_correct else 0

#         return {
#             "awarded_points": awarded,
#             "is_correct": is_correct,
#             "feedback": self.explanation or "",
#         }


class Choice(TimeStampModel):

    question = models.ForeignKey(
        MultipleChoiceQuestion,
        on_delete=models.CASCADE,
        related_name="choices",
    )

    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(
                fields=["question", "order"], name="unique_choice_order_per_question"
            )
        ]
