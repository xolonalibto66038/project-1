from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import TimeStampModel


class QuizQuestion(TimeStampModel):
    """
    Through model to link Quiz with Questions in a specific order
    """

    quiz = models.ForeignKey(
        "Quiz", on_delete=models.CASCADE, related_name="quiz_questions"
    )

    question_type = models.CharField(max_length=10, editable=False)

    # Generic relationship to any question type
    question_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    question_object_id = models.UUIDField(
        verbose_name=_("Object ID"), help_text=_("ID of the question")
    )
    question = GenericForeignKey("question_content_type", "question_object_id")

    # Order of question in the quiz
    order = models.PositiveIntegerField(default=1)

    # Optional: Override question points for this specific quiz
    points_override = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Override the default points for this question in this quiz",
    )

    class Meta:
        db_table = "quiz_questions"
        verbose_name = _("Quiz Question")
        verbose_name_plural = _("Quiz Questions")
        ordering = ["order", "-created_at"]
        unique_together = ["quiz", "question_content_type", "question_object_id"]
        indexes = [
            models.Index(fields=["quiz", "order"]),
        ]

    def __str__(self):
        return f"{self.quiz.title} - Question {self.order}"

    @property
    def effective_points(self):
        """Get the points for this question (override or default)"""
        return self.points_override or self.question.points
