# apps/accounts/models/student_profile.py

from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import TimeStampModel


class StudentProfile(TimeStampModel):
    """
    Extended profile for students.
    Created automatically on registration via signal.
    """

    user = models.OneToOneField(
        "accounts.CustomUser",
        on_delete=models.CASCADE,
        related_name="student_profile",
        verbose_name=_("User"),
        help_text=_("The user account associated with this student profile."),
    )
    grade = models.ForeignKey(
        "curriculum.Grade",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="students",
        verbose_name=_("Grade"),
        help_text=_("Current grade the student is enrolled in."),
    )
    specialty = models.ForeignKey(
        "curriculum.Specialty",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="students",
        verbose_name=_("Specialty"),
        help_text=_(
            "Filière for Secondaire students (e.g. Sciences Expérimentales). "
            "Leave blank for Primaire and Moyen students."
        ),
    )
    bio = models.TextField(
        blank=True,
        verbose_name=_("Bio"),
        help_text=_("Optional short student bio."),
    )

    class Meta:
        verbose_name = _("Student Profile")
        verbose_name_plural = _("Student Profiles")

    def __str__(self):
        return f"Student: {self.user.get_full_name()}"

    @property
    def full_name(self):
        return self.user.get_full_name()

    @property
    def level(self):
        """Convenience access to the student's level via grade."""
        return self.grade.level if self.grade else None
