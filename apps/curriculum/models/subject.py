from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from common.models import TimeStampModel


class Subject(TimeStampModel):
    level = models.ForeignKey(
        "Level",
        on_delete=models.CASCADE,
        related_name='subjects',
        verbose_name=_('Level'),
        help_text=_('The education level this subject belongs to. A subject is shared across all grades of a level.'),
    )
    name = models.CharField(
        max_length=100,
        verbose_name=_('Name'),
        help_text=_('Full subject name (e.g. "Mathématiques").'),
    )
    short_name = models.CharField(
        max_length=20,
        verbose_name=_('Short Name'),
        help_text=_('Abbreviated subject name used in UI (e.g. "Math").'),
    )
    slug = models.SlugField(
        max_length=50,
        unique=True,
        blank=True,
        verbose_name=_('Slug'),
        help_text=_('URL-friendly identifier, auto-generated from level and subject name.'),
    )
    icon = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Icon'),
        help_text=_('Icon class for UI display (e.g. FontAwesome class like "fa-calculator").'),
    )

    class Meta:
        unique_together = ('level', 'name')
        ordering = ['name']
        verbose_name = _('Subject')
        verbose_name_plural = _('Subjects')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.level.name}-{self.name}")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.level})"
