# apps/authentication/signals.py

from django.dispatch import receiver
from allauth.socialaccount.signals import social_account_added

from apps.accounts.choices import UserRole
from apps.accounts.models import StudentProfile, TeacherProfile


@receiver(social_account_added)
def handle_social_signup(sender, request, sociallogin, **kwargs):
    """
    Ensure profile exists after Google signup.
    accounts.signals handles this for email signup —
    this covers the social path.
    """
    user = sociallogin.user
    if user.role == UserRole.STUDENT:
        StudentProfile.objects.get_or_create(user=user)
    elif user.role == UserRole.TEACHER:
        TeacherProfile.objects.get_or_create(user=user)