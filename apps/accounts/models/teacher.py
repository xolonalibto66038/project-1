# apps/accounts/models/teacher_profile.py

from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import TimeStampModel


class TeacherProfile(TimeStampModel):
    """
    Extended profile for teachers.
    A teacher is scoped to a Level + Subject (not a specific Grade).
    e.g. A Maths teacher in Moyen can teach all AM grades.
    Created automatically on registration via signal.
    """

    user = models.OneToOneField(
        "accounts.CustomUser",
        on_delete=models.CASCADE,
        related_name="teacher_profile",
        verbose_name=_("User"),
        help_text=_("The user account associated with this teacher profile."),
    )
    level = models.ForeignKey(
        "curriculum.Level",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="teachers",
        verbose_name=_("Level"),
        help_text=_("The education level this teacher teaches (e.g. Moyen)."),
    )
    subject = models.ForeignKey(
        "curriculum.Subject",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="teachers",
        verbose_name=_("Subject"),
        help_text=_(
            "The subject this teacher specializes in. "
            "Must belong to the selected level."
        ),
    )
    bio = models.TextField(
        blank=True,
        verbose_name=_("Bio"),
        help_text=_("Optional teacher bio or professional description."),
    )
    is_verified_teacher = models.BooleanField(
        default=False,
        verbose_name=_("Is Verified Teacher"),
        help_text=_(
            "Designates whether this teacher has been verified by an admin. "
            "Only verified teachers can publish resources."
        ),
    )

    hour_price = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
        verbose_name=_("Hourly Price"),
        help_text=_("Price per hour for tutoring sessions."),
    )

    class Meta:
        verbose_name = _("Teacher Profile")
        verbose_name_plural = _("Teacher Profiles")

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.level and self.subject:
            if self.subject.level != self.level:
                raise ValidationError(
                    _("The selected subject does not belong to the selected level.")
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Teacher: {self.user.get_full_name()}"

    @property
    def full_name(self):
        return self.user.get_full_name()
