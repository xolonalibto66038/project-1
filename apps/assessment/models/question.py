from django.db import models
from django.utils.translation import gettext_lazy as _
from taggit.managers import TaggableManager

from apps.content.choices import DifficultyLevel
from common.models import TimeStampModel, UUIDTaggedItem

from ..choices import QuestionType


class BaseQuestion(TimeStampModel):
    """
    Abstract base class for all question types
    """

    # Basic fields
    title = models.CharField(max_length=200)
    question_text = models.TextField()
    points = models.PositiveIntegerField(default=1)
    question_type = models.CharField(
        max_length=10,
        choices=QuestionType.choices,
        editable=False,
        db_index=True,
    )

    # === TAGGING SYSTEM ===
    tags = TaggableManager(
        through=UUIDTaggedItem,
        blank=True,
        help_text=_(
            "Tags for categorizing and discovering questions "
            "(e.g., 'python', 'beginner', 'tutorial', 'exam-prep')"
        ),
        verbose_name=_("Tags"),
    )

    # Optional fields
    difficulty_level = models.CharField(
        max_length=10,
        choices=DifficultyLevel.choices,
        default=DifficultyLevel.MEDIUM,
    )

    # Metadata
    created_by = models.ForeignKey(
        "accounts.CustomUser",
        on_delete=models.CASCADE,
        related_name="%(class)s_related",
        null=True,
        blank=True,
        limit_choices_to={"role": "teacher"},
    )

    subject = models.ForeignKey(
        "curriculum.Subject",
        on_delete=models.CASCADE,
        related_name="%(class)s_questions",
        null=True,
        blank=True,
    )

    course = models.ForeignKey(
        "content.Course",
        on_delete=models.CASCADE,
        related_name="%(class)s_questions",
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def grade(self, answer):
        """
        Must return:
        {
            "awarded_points": float,
            "is_correct": bool,
            "feedback": str (optional)
        }
        """
        raise NotImplementedError
