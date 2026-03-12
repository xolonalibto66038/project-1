from django.db import models
from django.utils.translation import gettext_lazy as _

from .question import BaseQuestion


class EssayQuestion(BaseQuestion):
    """
    Text/Essay type questions where users provide written answers
    """

    # Text-specific fields
    max_length = models.PositiveIntegerField(
        default=500, help_text=_("Maximum character length for the answer")
    )
    min_length = models.PositiveIntegerField(
        default=10, help_text=_("Minimum character length for the answer")
    )

    # Expected answer for reference (optional for instructors)
    sample_answer = models.TextField(
        blank=True,
        help_text=_(
            "Sample or expected answer for instructor reference",
        ),
    )

    explanation = models.TextField(
        blank=True,
        help_text=_(
            "Optional explanation or additional context shown after answering."
        ),
    )

    # Auto-grading options
    is_auto_gradable = models.BooleanField(
        default=False,
        help_text=_("Whether this question can be auto-graded using keywords"),
    )
    keywords = models.TextField(
        blank=True,
        help_text=_("Comma-separated keywords for auto-grading (if enabled)"),
    )

    class Meta:
        db_table = "essay_questions"
        verbose_name = _("Essay Question")
        verbose_name_plural = _("Essay Questions")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["question_type"]),
            models.Index(fields=["difficulty_level"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["created_by"]),
        ]

    def __str__(self):
        return f"{self.title} (Text)"

    def save(self, *args, **kwargs):
        self.question_type = "essay"
        super().save(*args, **kwargs)

    def get_keywords_list(self):
        if not self.keywords:
            return []

        return [
            keyword.strip().lower()
            for keyword in self.keywords.split(",")
            if keyword.strip()
        ]

    def validate_answer_length(self, answer_text):
        """Validate if answer meets length requirements"""
        answer_length = len(answer_text.strip())
        return self.min_length <= answer_length <= self.max_length

    def get_question_type(self):
        return "essay_question"  # ou une autre logique

    def grade(self, answer):
        if not isinstance(answer, str):
            return {
                "awarded_points": 0,
                "is_correct": False,
                "feedback": "Invalid answer format.",
            }

        if not self.validate_answer_length(answer):
            return {
                "awarded_points": 0,
                "is_correct": False,
                "feedback": "Answer does not meet length requirements.",
            }

        if not self.is_auto_gradable:
            return {
                "awarded_points": 0,
                "is_correct": False,
                "feedback": "Pending manual review.",
            }

        keywords = self.get_keywords_list()
        answer_lower = answer.lower()

        matches = sum(1 for keyword in keywords if keyword in answer_lower)

        if not keywords:
            return {
                "awarded_points": 0,
                "is_correct": False,
                "feedback": "No keywords configured.",
            }

        score_ratio = matches / len(keywords)
        awarded = round(self.points * score_ratio, 2)

        return {
            "awarded_points": awarded,
            "is_correct": score_ratio >= 0.8,  # "is_correct": score_ratio == 1,
            "feedback": self.explanation or "",
        }
