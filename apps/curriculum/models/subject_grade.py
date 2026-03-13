from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from common.models import TimeStampModel


class GradeSubject(TimeStampModel):
    grade = models.ForeignKey(
        "Grade",
        on_delete=models.CASCADE,
        related_name="grade_subjects",
        verbose_name=_("Grade"),
        help_text=_("The grade in which this subject is taught."),
    )
    subject = models.ForeignKey(
        "Subject",
        on_delete=models.CASCADE,
        related_name="grade_subjects",
        verbose_name=_("Subject"),
        help_text=_("The subject taught in this grade."),
    )
    specialty = models.ForeignKey(
        "Specialty",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="grade_subjects",
        verbose_name=_("Specialty"),
        help_text=_(
            "The filière this subject is restricted to. Leave blank if the subject applies to all specialties of this grade."
        ),
    )
    slug = models.SlugField(unique=True, editable=False, null=True, blank=True)
    is_active = models.BooleanField(default=True, blank=True, null=True)

    class Meta:
        unique_together = ("grade", "subject", "specialty")
        verbose_name = _("Grade Subject")
        verbose_name_plural = _("Grade Subjects")
        constraints = [
            models.UniqueConstraint(
                fields=["grade", "subject", "specialty"],
                name="unique_grade_subject_specialty",
            )
        ]

    def __str__(self):
        spec = f" [{self.specialty.short_name}]" if self.specialty else ""
        return f"{self.grade.short_name} - {self.subject.short_name}{spec}"

    def save(self, *args, **kwargs):
        if not self.slug:
            spec = self.specialty.short_name if self.specialty else "all"
            self.slug = slugify(
                f"{self.grade.short_name}-{self.subject.short_name}-{spec}"
            )
        # spec = self.specialty.short_name if self.specialty else "all"
        # self.slug = slugify(f"{self.grade.short_name}-{self.subject.short_name}-{spec}")
        super().save(*args, **kwargs)
