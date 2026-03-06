# apps/authentication/adapters.py

from django.conf import settings
from django.http import HttpRequest

from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.core.exceptions import ImmediateHttpResponse

from .exceptions import RoleRequiredException


class CustomAccountAdapter(DefaultAccountAdapter):
    """
    Custom allauth adapter.
    - Enforces role selection on signup
    - Role-based redirect after login
    """

    def get_login_redirect_url(self, request):
        """Redirect based on user role after login."""
        user = request.user
        if not user.is_authenticated:
            return settings.LOGIN_REDIRECT_URL
        if user.is_staff or user.is_superuser:
            return '/admin/'
        return '/dashboard/'

    def save_user(self, request, user, form, commit=True):
        """
        Extend default save_user to persist role and profile fields
        from the registration form.
        """
        user = super().save_user(request, user, form, commit=False)

        # role comes from the custom signup form
        user.role = form.cleaned_data.get('role', '')

        if commit:
            user.save()
        return user

    def send_confirmation_mail(self, request, emailconfirmation, signup):
        """Hook — add custom context if needed for email templates."""
        super().send_confirmation_mail(request, emailconfirmation, signup)


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom social account adapter for Google login.
    - Auto-fills profile fields from Google data
    - Assigns default role if not already set
    """

    def pre_social_login(self, request, sociallogin):
        """
        Called after OAuth but before login/signup is finalized.
        Link social account to existing email if user already registered.
        """
        from apps.accounts.models.custom_user import CustomUser

        if sociallogin.is_existing:
            return

        try:
            email = sociallogin.account.extra_data.get('email', '').lower()
            if not email:
                return
            existing = CustomUser.objects.get(email=email)
            sociallogin.connect(request, existing)
        except CustomUser.DoesNotExist:
            pass

    def save_user(self, request, sociallogin, form=None):
        """Auto-fill first_name, last_name, avatar from Google profile."""
        user = super().save_user(request, sociallogin, form)

        extra = sociallogin.account.extra_data

        if not user.first_name:
            user.first_name = extra.get('given_name', '')
        if not user.last_name:
            user.last_name = extra.get('family_name', '')

        # role defaults to student for social signups
        if not user.role:
            from apps.accounts.choices import UserRole
            role       = request.session.pop('pending_role', UserRole.STUDENT)
            user.role  = role

        user.is_verified = True   # Google already verified the email
        user.save()

        self._ensure_profile(user)

        return user

    def is_auto_signup_allowed(self, request, sociallogin):
        """Allow auto-signup for Google — email is pre-verified."""
        return True
    
    def _ensure_profile(self, user):
        """Guarantee profile exists regardless of signal timing."""
        from apps.accounts.choices import UserRole
        from apps.accounts.models import StudentProfile, TeacherProfile

        if user.role == UserRole.STUDENT:
            StudentProfile.objects.get_or_create(user=user)
        elif user.role == UserRole.TEACHER:
            TeacherProfile.objects.get_or_create(user=user)