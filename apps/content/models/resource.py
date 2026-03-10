import os
import hashlib
import mimetypes

from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from taggit.managers import TaggableManager

from common.models import UUIDTaggedItem, TimeStampModel
from ..choices import DifficultyLevel, ResourceStatus, ResourceType, Term

User = get_user_model()


class Resource(TimeStampModel):
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

    # Automatically populated file metadata fields
    file_size = models.PositiveIntegerField(
        editable=False,
        null=True,
        blank=True,
        verbose_name=_("File Size (bytes)"),
        help_text=_("File size in bytes, automatically calculated"),
    )
    original_filename = models.CharField(
        max_length=255,
        editable=False,
        blank=True,
        verbose_name=_("Original Filename"),
        help_text=_("Original name of the uploaded file"),
    )
    file_extension = models.CharField(
        max_length=10,
        editable=False,
        blank=True,
        verbose_name=_("File Extension"),
        help_text=_("File extension (without dot)"),
    )
    file_mimetype = models.CharField(
        max_length=100,
        editable=False,
        blank=True,
        verbose_name=_("MIME Type"),
        help_text=_("File MIME type for proper handling"),
    )
    file_hash = models.CharField(
        max_length=64,
        editable=False,
        blank=True,
        verbose_name=_("File Hash (SHA-256)"),
        help_text=_("SHA-256 hash for file integrity verification"),
        db_index=True,  # Index for duplicate detection
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

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='resources',
        verbose_name=_('Author'),
        help_text=_('The teacher who created this resource.'),
        limit_choices_to={"role": "teacher"}
    )

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
        # Inherit course term automatically
        if self.course:
            self.term = self.course.term
        if not self.slug:
            parent_slug = self.course.slug if self.course else self.subject.slug
            self.slug = slugify(f"{parent_slug}-{self.resource_type}-{self.title}")
        
        # Extract custom parameters
        skip_validation = kwargs.pop("skip_validation", False)

        if not skip_validation:
            self.full_clean()

        file_changed = False

        if self.pk:
            old = self.__class__.objects.filter(pk=self.pk).only("file").first()
            if old and old.file != self.file:
                file_changed = True
        else:
            file_changed = bool(self.file)

        super().save(*args, **kwargs)

        if file_changed and self.file:
            self._process_file_metadata()
            super().save(
                update_fields=[
                    "file_size",
                    "original_filename",
                    "file_extension",
                    "file_mimetype",
                    "file_hash",
                ]
            )

    def delete(self, *args, **kwargs):
        """Delete file when model instance is deleted"""
        if self.file and os.path.isfile(self.file.path):
            # os.remove(self.file.path)
            self.file.delete(save=False)
        if self.solution_file and os.path.isfile(self.solution_file.path):
            # os.remove(self.solution_file.path)
            self.solution_file.delete(save=False)
        super().delete(*args, **kwargs)

    def _process_file_metadata(self):
        """Extract and store file metadata."""
        try:
            # Basic file information
            self.file_size = self.file.size
            self.original_filename = os.path.basename(self.file.name)

            # Extract extension
            _, ext = os.path.splitext(self.original_filename)
            self.file_extension = ext.lstrip(".").lower()

            # Determine MIME type
            # mime = magic.from_buffer(self.file.read(2048), mime=True)
            # self.file.seek(0)
            self.file_mimetype = (
                mimetypes.guess_type(self.original_filename)[0]
                or "application/octet-stream"
            )

            # Calculate file hash for integrity checking
            self._calculate_file_hash()

        except Exception as ex:
            # logger.error(f"Error processing file metadata for {self.id}: {e}")
            raise ValidationError(_(f"Error processing uploaded file. Error : {str(ex)}"))

    def _calculate_file_hash(self):
        """Calculate SHA-256 hash of the file content."""
        sha256_hash = hashlib.sha256()

        # Reset file pointer to beginning
        self.file.seek(0)

        # Read file in chunks to handle large files efficiently
        for chunk in self.file.chunks():
            sha256_hash.update(chunk)

        self.file_hash = sha256_hash.hexdigest()

        # Reset file pointer for any subsequent operations
        self.file.seek(0)

    def __str__(self):
        return f"[{self.get_resource_type_display()}] {self.title}"

    def clean(self):
        if self.solution_file and not self.has_solution:
            raise ValidationError(
                _('has_solution must be True when a solution file is attached.')
            )
        # Resource inside course must match course term
        if self.course:
            if self.term and self.term != self.course.term:
                raise ValidationError(
                    {
                        "term": _(
                            "Resource term must match the Course term (%(term)s)."
                        ) % {"term": self.course.get_term_display()}
                    }
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