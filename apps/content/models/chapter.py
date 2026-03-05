from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from apps.curriculum.models import GradeSubject
from ..choices import DifficultyLevel, ResourceStatus, ResourceType, Term


class Chapter(models.Model):
    """
    A chapter belongs to a GradeSubject.
    e.g. "Les Fractions" in Maths / 3AM
    """

    grade_subject = models.ForeignKey(
        "curriculum.GradeSubject",
        on_delete=models.CASCADE,
        related_name='chapters',
        verbose_name=_('Grade Subject'),
        help_text=_('The grade/subject combination this chapter belongs to.'),
    )
    title = models.CharField(
        max_length=200,
        verbose_name=_('Title'),
        help_text=_('Full chapter title (e.g. "Les Fractions").'),
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
        help_text=_('Display order of this chapter within the grade subject.'),
    )
    term = models.CharField(
        max_length=10,
        choices=Term.choices,
        verbose_name=_('Term'),
        help_text=_('The school term (trimester) this chapter is taught in.'),
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Description'),
        help_text=_('Optional short description or learning objectives for this chapter.'),
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Is Active'),
        help_text=_('Inactive chapters are hidden from students.'),
    )

    class Meta:
        ordering = ['grade_subject', 'order']
        unique_together = ('grade_subject', 'order')
        verbose_name = _('Chapter')
        verbose_name_plural = _('Chapters')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(
                f"{self.grade_subject.grade.short_name}"
                f"-{self.grade_subject.subject.short_name}"
                f"-{self.title}"
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.grade_subject} – {self.title}"