from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from common.models import TimeStampModel


class Grade(TimeStampModel):
    level = models.ForeignKey(
        "Level",
        on_delete=models.CASCADE,
        related_name='grades',
        verbose_name=_('Level'),
        help_text=_('The education level this grade belongs to.'),
    )
    name = models.CharField(
        max_length=100,
        verbose_name=_('Name'),
        help_text=_('Full grade name (e.g. "1ère Année Primaire").'),
    )
    short_name = models.CharField(
        max_length=20,
        verbose_name=_('Short Name'),
        help_text=_('Abbreviated grade name used in UI and slugs (e.g. "1AP").'),
    )
    slug = models.SlugField(
        max_length=50,
        unique=True,
        blank=True,
        verbose_name=_('Slug'),
        help_text=_('URL-friendly identifier, auto-generated from the short name.'),
    )
    order = models.PositiveSmallIntegerField(
        verbose_name=_('Order'),
        help_text=_('Display order within the level (e.g. 1 for 1ère Année).'),
    )

    class Meta:
        ordering = ['level__order', 'order']
        unique_together = ('level', 'order')
        verbose_name = _('Grade')
        verbose_name_plural = _('Grades')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.short_name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.short_name