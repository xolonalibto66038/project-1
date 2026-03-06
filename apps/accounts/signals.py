# apps/accounts/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import CustomUser, StudentProfile, TeacherProfile
from .choices import UserRole


@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    """Auto-create the appropriate profile on user creation."""
    if not created:
        return
    if instance.role == UserRole.STUDENT:
        StudentProfile.objects.get_or_create(user=instance)
    elif instance.role == UserRole.TEACHER:
        TeacherProfile.objects.get_or_create(user=instance)