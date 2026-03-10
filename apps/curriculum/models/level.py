from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from common.models import TimeStampModel

from ..choices import LevelChoices


class Level(TimeStampModel):
    name = models.CharField(
        max_length=50,
        choices=LevelChoices.choices,
        unique=True,
        verbose_name=_("Name"),
        help_text=_("The education level (e.g. Primaire, Moyen, Secondaire)."),
    )
    slug = models.SlugField(
        max_length=50,
        unique=True,
        blank=True,
        verbose_name=_("Slug"),
        help_text=_("URL-friendly identifier, auto-generated from the name."),
    )
    order = models.PositiveSmallIntegerField(
        verbose_name=_("Order"),
        help_text=_(
            "Controls the display order of levels (e.g. 1=Primaire, 2=Moyen, 3=Secondaire)."
        ),
    )

    class Meta:
        ordering = ["order"]
        verbose_name = _("Level")
        verbose_name_plural = _("Levels")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.get_name_display())
        super().save(*args, **kwargs)

    def __str__(self):
        return self.get_name_display()
