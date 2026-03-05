from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from common.models import TimeStampModel


class Specialty(TimeStampModel):
    grade = models.ForeignKey(
        "Grade",
        on_delete=models.CASCADE,
        related_name='specialties',
        verbose_name=_('Grade'),
        help_text=_('The Secondaire grade this specialty (filière) belongs to.'),
    )
    name = models.CharField(
        max_length=100,
        verbose_name=_('Name'),
        help_text=_('Full specialty name (e.g. "Sciences Expérimentales").'),
    )
    short_name = models.CharField(
        max_length=20,
        verbose_name=_('Short Name'),
        help_text=_('Abbreviated specialty name used in UI and slugs (e.g. "SE").'),
    )
    slug = models.SlugField(
        max_length=50,
        unique=True,
        blank=True,
        verbose_name=_('Slug'),
        help_text=_('URL-friendly identifier, auto-generated from grade and short name.'),
    )

    class Meta:
        unique_together = ('grade', 'name')
        verbose_name = _('Specialty')
        verbose_name_plural = _('Specialties')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.grade.short_name}-{self.short_name}")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.grade.short_name} – {self.short_name}"