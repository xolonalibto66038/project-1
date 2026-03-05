from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from taggit.managers import TaggableManager

from common.models import UUIDTaggedItem
from ..choices import DifficultyLevel, ResourceStatus, ResourceType, Term


class Resource(models.Model):
    """
    A resource is the atomic content unit attached to a course.
    Covers: Lesson, Exercise, Homework, Test, Exam.
    Type-specific attributes are stored in `metadata` (JSONField).

    metadata examples:
      Lesson:   {}
      Exercise: {"total_marks": 20}
      Homework: {"due_days": 7}
      Test:     {"duration_minutes": 60, "total_marks": 20}
      Exam:     {"duration_minutes": 120, "total_marks": 20, "coefficient": 2}
    """

    course = models.ForeignKey(
        "Course",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='resources',
        verbose_name=_('Course'),
        help_text=_('The course this resource belongs to.'),
    )
    subject = models.ForeignKey(
        "curriculum.Subject",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="resources",
        verbose_name=_("Subject"),
        help_text=_(
            "Subject to which this resource belongs (mutually exclusive with course)"
        ),
        db_index=True,
    )
    title = models.CharField(
        max_length=200,
        verbose_name=_('Title'),
        help_text=_('Title of the resource.'),
    )
    slug = models.SlugField(
        max_length=220,
        unique=True,
        blank=True,
        verbose_name=_('Slug'),
        help_text=_('URL-friendly identifier, auto-generated from the title.'),
    )
    resource_type = models.CharField(
        max_length=20,
        choices=ResourceType.choices,
        verbose_name=_('Resource Type'),
        help_text=_('Type of resource: lesson, exercise, homework, test or exam.'),
    )
    status = models.CharField(
        max_length=20,
        choices=ResourceStatus.choices,
        default=ResourceStatus.DRAFT,
        verbose_name=_('Status'),
        help_text=_('Draft resources are only visible to their author.'),
    )
    difficulty = models.CharField(
        max_length=10,
        choices=DifficultyLevel.choices,
        default=DifficultyLevel.MEDIUM,
        verbose_name=_('Difficulty'),
        help_text=_('Difficulty level of this specific resource.'),
    )
    order = models.PositiveSmallIntegerField(
        default=0,
        verbose_name=_('Order'),
        help_text=_('Display order within the course.'),
    )
    term = models.CharField(
        max_length=10,
        choices=Term.choices,
        verbose_name=_('Term'),
        help_text=_('The school term (trimester) this chapter is taught in.'),
    )
    file = models.FileField(
        upload_to='resources/%Y/%m/',
        blank=True,
        null=True,
        verbose_name=_('File'),
        help_text=_('Uploaded file (PDF, Word, video, etc.).'),
    )
    solution_file = models.FileField(
        upload_to='solutions/%Y/%m/',
        null=True,
        blank=True,
        verbose_name=_("Solution"),
        help_text=_("File containing the resource solution"),
    )

    has_solution = models.BooleanField(
        default=False,
        verbose_name=_("Has Solution"),
        help_text=_("Indicates whether this resource has an associated solution file"),
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Metadata'),
        help_text=_(
            'Type-specific attributes. '
            'e.g. {"duration_minutes": 60, "total_marks": 20} for a test.'
        ),
    )
    is_free = models.BooleanField(
        default=True,
        verbose_name=_('Is Free'),
        help_text=_('Free resources are accessible to guest users.'),
    )

    tags = TaggableManager(
        through=UUIDTaggedItem,
        blank=True,
        help_text=_(
            "Tags for categorizing and discovering resources "
            "(e.g., 'python', 'beginner', 'tutorial', 'exam-prep')"
        ),
        verbose_name=_("Tags"),
    )

    # author = models.ForeignKey(
    #     settings.AUTH_USER_MODEL,
    #     on_delete=models.SET_NULL,
    #     null=True,
    #     related_name='resources',
    #     verbose_name=_('Author'),
    #     help_text=_('The teacher who created this resource.'),
    # )

    class Meta:
        ordering = ['course', 'order']
        verbose_name = _('Resource')
        verbose_name_plural = _('Resources')

        constraints = [
            # Ensure exactly one parent relationship
            models.CheckConstraint(
                condition=(
                    models.Q(course__isnull=False, subject__isnull=True)
                    | models.Q(course__isnull=True, subject__isnull=False)
                ),
                name="resource_exactly_one_parent",
                violation_error_message=_(
                    "Resource must belong to exactly one course or subject"
                ),
            ),
            # Ensure resource type matches parent entity
            models.CheckConstraint(
                condition=(
                    # Course resources can only be lesson, exercise, or homework
                    models.Q(
                        course__isnull=False,
                        resource_type__in=ResourceType.get_course_values(),
                    )
                    # Subject resources can only be test or exam
                    | models.Q(
                        subject__isnull=False, resource_type__in=ResourceType.get_subject_values()
                    )
                ),
                name="resource_type_matches_parent",
                violation_error_message=_(
                    "Resource type must match parent entity requirements"
                ),
            ),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            parent_slug = self.course.slug if self.course else self.subject.slug
            self.slug = slugify(f"{parent_slug}-{self.resource_type}-{self.title}")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.get_resource_type_display()}] {self.title}"

    def clean(self):
        if self.solution_file and not self.has_solution:
            raise ValidationError(
                _('has_solution must be True when a solution file is attached.')
            )

    # ── Metadata helpers ──

    @property
    def duration_minutes(self):
        return self.metadata.get('duration_minutes')

    @property
    def total_marks(self):
        return self.metadata.get('total_marks')

    @property
    def coefficient(self):
        return self.metadata.get('coefficient')

    @property
    def due_days(self):
        return self.metadata.get('due_days')