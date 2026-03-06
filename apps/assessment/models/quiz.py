from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from common.models import TimeStampModel


class Quiz(TimeStampModel):
    """
    Container for multiple questions that make up a quiz/exam
    """

    # Basic information
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    instructions = models.TextField(
        blank=True,
        help_text="Instructions shown to students before taking the quiz",
    )

    # Quiz settings
    time_limit = models.PositiveIntegerField(
        null=True, blank=True, help_text="Time limit in minutes (null = no time limit)"
    )

    max_attempts = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Maximum number of attempts allowed per user",
    )

    passing_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=70.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Minimum percentage score to pass",
    )

    # Availability settings
    is_published = models.BooleanField(
        default=False, help_text="Whether the quiz is visible to students"
    )

    start_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the quiz becomes available (null = available immediately)",
    )

    end_date = models.DateTimeField(
        null=True, blank=True, help_text="When the quiz closes (null = no end date)"
    )

    # Quiz behavior
    randomize_questions = models.BooleanField(
        default=False, help_text="Randomize question order for each attempt"
    )

    show_results_immediately = models.BooleanField(
        default=True, help_text="Show results to student immediately after submission"
    )

    allow_review = models.BooleanField(
        default=True,
        help_text="Allow students to review their answers after submission",
    )

    # Metadata
    created_by = models.ForeignKey(
        "accounts.CustomUser",
        on_delete=models.CASCADE,
        related_name="created_quizzes",
        null=True,
        blank=True,
        limit_choices_to={"role": "teacher"},
    )

    subject = models.ForeignKey(
        "curriculum.Subject",
        on_delete=models.CASCADE,
        related_name="quizzes",
        null=True,
        blank=True,
    )

    course = models.ForeignKey(
        "content.Course",
        on_delete=models.CASCADE,
        related_name="quizzes",
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "quizzes"
        ordering = ["-created_at"]
        verbose_name = _("Quiz")
        verbose_name_plural = _("Quizzes")
        constraints = [
            models.CheckConstraint(
                check=(
                    # Exactly one must be set
                    (Q(subject__isnull=False) & Q(course__isnull=True))
                    | (Q(subject__isnull=True) & Q(course__isnull=False))
                ),
                name="quiz_belongs_to_exactly_one_parent",
            )
        ]

    def __str__(self):
        return self.title

    def clean(self):
        if not self.subject and not self.course:
            raise ValidationError("Quiz must belong to either a subject or a course.")

        if self.subject and self.course:
            raise ValidationError("Quiz cannot belong to both subject and course.")

    @property
    def total_points(self):
        """Calculate total possible points for this quiz"""
        # return sum(
        #     qq.effective_points
        #     for qq in self.quiz_questions.select_related("question_content_type")
        # )
        return sum(qq.effective_points for qq in self.quiz_questions.all())

    @property
    def question_count(self):
        """Get total number of questions in this quiz"""
        return self.quiz_questions.count()

    @property
    def is_available(self):
        """Check if quiz is currently available for taking"""
        from django.utils import timezone

        now = timezone.localtime()

        if not self.is_published:
            return False

        if self.start_date and now < self.start_date:
            return False

        if self.end_date and now > self.end_date:
            return False

        return True

    def can_user_attempt(self, user):
        """Check if user can take/retake this quiz"""
        if not self.is_available:
            return False, "Quiz is not available"

        attempts_count = self.quiz_attempts.filter(student=user).count()
        
        if attempts_count >= self.max_attempts:
            return False, f"Maximum attempts ({self.max_attempts}) reached"

        return True, "Can attempt"

    def get_user_best_score(self, user):
        """Get user's best score percentage for this quiz"""
        attempts = self.attempts.filter(student=user, is_completed=True)
        if not attempts.exists():
            return None

        best_attempt = attempts.order_by("-score_percentage").first()
        return best_attempt.score_percentage

    def get_user_attempts_count(self, user):
        """Get number of attempts user has made"""
        return self.attempts.filter(student=user).count()
