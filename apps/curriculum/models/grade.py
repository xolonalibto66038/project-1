from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from common.models import TimeStampModel


class Grade(TimeStampModel):
    level = models.ForeignKey(
        "Level",
        on_delete=models.CASCADE,
        related_name="grades",
        verbose_name=_("Level"),
        help_text=_("The education level this grade belongs to."),
    )
    name = models.CharField(
        max_length=100,
        verbose_name=_("Name"),
        help_text=_('Full grade name (e.g. "1ère Année Primaire").'),
    )
    short_name = models.CharField(
        max_length=20,
        verbose_name=_("Short Name"),
        help_text=_('Abbreviated grade name used in UI and slugs (e.g. "1AP").'),
    )
    slug = models.SlugField(
        max_length=50,
        unique=True,
        blank=True,
        verbose_name=_("Slug"),
        help_text=_("URL-friendly identifier, auto-generated from the short name."),
    )
    order = models.PositiveSmallIntegerField(
        verbose_name=_("Order"),
        help_text=_("Display order within the level (e.g. 1 for 1ère Année)."),
    )

    class Meta:
        ordering = ["level__order", "order"]
        unique_together = ("level", "order")
        verbose_name = _("Grade")
        verbose_name_plural = _("Grades")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.short_name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.short_name

    @staticmethod
    def _display_name(obj: object) -> str:
        """
        Resolve the best human-readable label for any curriculum model.

        Priority:
        1. get_name_display()  — present when ``name`` is a choices field (e.g. Level)
        2. name                — full label (e.g. Grade.name = "1ère Année Primaire")
        3. short_name          — compact fallback (e.g. Grade.short_name = "1AP")
        4. str(obj)            — last resort, always defined
        """
        if callable(getattr(obj, "get_name_display", None)):
            return obj.get_name_display()
        if hasattr(obj, "name") and obj.name:
            return obj.name
        if hasattr(obj, "short_name") and obj.short_name:
            return obj.short_name
        return str(obj)
