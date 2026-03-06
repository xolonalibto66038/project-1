from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from common.models import TimeStampModel
from ..choices import DifficultyLevel, Term


class Course(TimeStampModel):
    """
    A course is a unit of content.
    It belongs to either:
      - A Chapter (standard case)
      - A GradeSubject directly (standalone course with no chapter)
    Never both.
    """

    chapter = models.ForeignKey(
        "Chapter",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='courses',
        verbose_name=_('Chapter'),
        help_text=_('The chapter this course belongs to. Leave blank for standalone courses.'),
    )
    grade_subject = models.ForeignKey(
        "curriculum.GradeSubject",
        null=True,                  # ✅ nullable — only set when chapter is null
        blank=True,
        on_delete=models.CASCADE,
        related_name='courses',     # ✅ fixed related_name
        verbose_name=_('Grade Subject'),
        help_text=_(
            'The grade/subject this course belongs to directly. '
            'Only set when the course has no chapter.'
        ),
    )
    title = models.CharField(
        max_length=200,
        verbose_name=_('Title'),
        help_text=_('Full course title.'),
    )
    slug = models.SlugField(
        max_length=220,
        unique=True,
        blank=True,
        verbose_name=_('Slug'),
        help_text=_('URL-friendly identifier, auto-generated from the title.'),
    )
    order = models.PositiveSmallIntegerField(
        verbose_name=_('Order'),
        help_text=_('Display order within the chapter or grade subject.'),
    )
    term = models.CharField(
        max_length=10,
        choices=Term.choices,
        null=True,              # ✅ optional when chapter exists (inherited)
        blank=True,
        verbose_name=_('Term'),
        help_text=_(
            'Required only for standalone courses (no chapter). '
            'Chapter-based courses inherit the term from their chapter.'
        ),
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Description'),
        help_text=_('Optional overview or learning objectives for this course.'),
    )
    difficulty = models.CharField(
        max_length=10,
        choices=DifficultyLevel.choices,
        default=DifficultyLevel.MEDIUM,
        verbose_name=_('Difficulty'),
        help_text=_('Overall difficulty level of this course.'),
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Is Active'),
        help_text=_('Inactive courses are hidden from students.'),
    )

    class Meta:
        ordering = ['chapter', 'order']
        verbose_name = _('Course')
        verbose_name_plural = _('Courses')
        constraints = [
            # ✅ Must belong to exactly one parent
            models.CheckConstraint(
                condition=(
                    models.Q(chapter__isnull=False, grade_subject__isnull=True)
                    | models.Q(chapter__isnull=True, grade_subject__isnull=False)
                ),
                name='course_exactly_one_parent',
                violation_error_message=_(
                    'A course must belong to either a chapter or a grade subject, not both.'
                ),
            ),
            # ✅ Standalone courses (no chapter) must have a term
            models.CheckConstraint(
                condition=(
                    models.Q(chapter__isnull=False)          # chapter-based: term optional
                    | models.Q(chapter__isnull=True, term__isnull=False)  # standalone: term required
                ),
                name='course_standalone_requires_term',
                violation_error_message=_(
                    'Standalone courses (without a chapter) must have a term assigned.'
                ),
            ),
        ]

    def clean(self):
        from django.core.exceptions import ValidationError
        # Both null
        if not self.chapter and not self.grade_subject:
            raise ValidationError(
                _('A course must belong to either a chapter or a grade subject.')
            )
        # Both set
        if self.chapter and self.grade_subject:
            raise ValidationError(
                _('A course cannot belong to both a chapter and a grade subject.')
            )
        # Standalone must have term
        if not self.chapter and not self.term:
            raise ValidationError(
                _('Standalone courses must have a term assigned.')
            )
        # grade_subject must match chapter's grade_subject
        if self.chapter and self.grade_subject:
            if self.chapter.grade_subject != self.grade_subject:
                raise ValidationError(
                    _('The grade subject must match the chapter\'s grade subject.')
                )

        # Course inside chapter must match chapter term
        if self.chapter:
            if self.term and self.term != self.chapter.term:
                raise ValidationError(
                    {
                        "term": _(
                            "Course term must match the chapter term (%(term)s)."
                        ) % {"term": self.chapter.get_term_display()}
                    }
                )

    def save(self, *args, **kwargs):
        # Inherit chapter term automatically
        if self.chapter:
            self.term = self.chapter.term

        if not self.slug:
            parent_slug = self.chapter.slug if self.chapter else (
                f"{self.grade_subject.grade.short_name}"
                f"-{self.grade_subject.subject.short_name}"
            )
            self.slug = slugify(f"{parent_slug}-{self.title}")
        super().save(*args, **kwargs)

    def __str__(self):
        parent = self.chapter or self.grade_subject
        return f"{parent} - {self.title}"

    @property
    def effective_term(self):
        """Returns term from chapter if available, otherwise own term."""
        return self.chapter.term if self.chapter else self.term

    @property
    def effective_grade_subject(self):
        """Returns grade_subject from chapter if available, otherwise own."""
        return self.chapter.grade_subject if self.chapter else self.grade_subject