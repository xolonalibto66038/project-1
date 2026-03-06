from django.shortcuts import redirect


class OnboardingMiddleware:
    """
    Redirects authenticated, non-staff users with incomplete profiles
    to /onboarding/ before they can access anything else.
    """

    EXEMPT_PREFIXES = (
        '/onboarding/',
        '/accounts/',
        '/admin/',
        '/ajax/',
        '/static/',
        '/media/',
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if self._should_redirect(request):
            return redirect('onboarding')
        return self.get_response(request)

    def _should_redirect(self, request):
        if not request.user.is_authenticated:
            return False
        if request.user.is_staff or request.user.is_superuser:
            return False
        if any(request.path.startswith(p) for p in self.EXEMPT_PREFIXES):
            return False
        return not self._profile_complete(request.user)

    def _profile_complete(self, user):
        from apps.accounts.choices import UserRole
        if user.role == UserRole.STUDENT:
            profile = getattr(user, 'student_profile', None)
            return profile and profile.grade is not None
        if user.role == UserRole.TEACHER:
            profile = getattr(user, 'teacher_profile', None)
            return (
                profile and
                profile.level is not None and
                profile.subject is not None
            )
        return True