from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.utils.html import format_html

from common.models import TimeStampModel
from ..choices import Gender, UserRole, Wilaya
from ..managers import CustomUserManager


class CustomUser(AbstractUser, TimeStampModel):
    """
    Custom user model using email as the primary authentication field.
    username is kept for display/URL purposes only.
    """

    # ── Disable unused AbstractUser fields ──
    username    = None  # replaced by email auth
    first_name  = models.CharField(
        max_length=100,
        verbose_name=_('First Name'),
        help_text=_('User\'s first name.'),
    )
    last_name   = models.CharField(
        max_length=100,
        verbose_name=_('Last Name'),
        help_text=_('User\'s last name.'),
    )

    # ── Auth ──
    email = models.EmailField(
        unique=True,
        verbose_name=_('Email Address'),
        help_text=_('Used as the login identifier.'),
    )

    # ── Role ──
    role = models.CharField(
        max_length=10,
        choices=UserRole.choices,
        verbose_name=_('Role'),
        help_text=_('Determines whether the user is a Student or Teacher.'),
    )

    # ── Profile fields ──
    avatar = models.ImageField(
        upload_to='avatars/%Y/%m/',
        null=True,
        blank=True,
        verbose_name=_('Avatar'),
        help_text=_('Profile picture.'),
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Phone Number'),
        help_text=_('Algerian phone number (e.g. 0555 123 456).'),
    )
    date_of_birth = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Date of Birth'),
        help_text=_('Used for age verification and personalization.'),
    )
    gender = models.CharField(
        max_length=10,
        choices=Gender.choices,
        blank=True,
        verbose_name=_('Gender'),
        help_text=_('Optional gender field.'),
    )
    wilaya = models.CharField(
        max_length=2,
        choices=Wilaya.choices,
        blank=True,
        verbose_name=_('Wilaya'),
        help_text=_('Algerian province of residence.'),
    )

    # ── Account state ──
    is_verified = models.BooleanField(
        default=False,
        verbose_name=_('Is Verified'),
        help_text=_('Designates whether the user has verified their email address.'),
    )

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = CustomUserManager()

    class Meta:
        verbose_name        = _('User')
        verbose_name_plural = _('Users')
        ordering            = ['-date_joined']

    def __str__(self):
        return f"{self.get_full_name()} <{self.email}>"

    @property
    def is_student(self):
        return self.role == UserRole.STUDENT

    @property
    def is_teacher(self):
        return self.role == UserRole.TEACHER

    @property
    def profile(self):
        """Returns the related profile based on role."""
        if self.is_student:
            return getattr(self, 'student_profile', None)
        if self.is_teacher:
            return getattr(self, 'teacher_profile', None)
        return None

    @property
    def avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return None

    @property
    def avatar_display(self):
        if self.avatar:
            return format_html(
                '<img src="{}" style="width:36px;height:36px;border-radius:50%;object-fit:cover;">',
                self.avatar.url
            )

        initials = f"{self.first_name[:1]}{self.last_name[:1]}".upper()

        return format_html(
            '<div style="width:36px;height:36px;border-radius:50%;background:#007bff;color:#fff;display:flex;align-items:center;justify-content:center;font-weight:bold;font-size:0.8em;">{}</div>',
            initials
        )