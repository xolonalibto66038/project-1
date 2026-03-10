# apps/authentication/decorators.py

from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _


def student_required(view_func):
    """Allows access only to authenticated students."""

    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_student:
            raise PermissionDenied(_("This page is for students only."))
        return view_func(request, *args, **kwargs)

    return wrapper


def teacher_required(view_func):
    """Allows access only to authenticated teachers."""

    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_teacher:
            raise PermissionDenied(_("This page is for teachers only."))
        return view_func(request, *args, **kwargs)

    return wrapper


def verified_teacher_required(view_func):
    """Allows access only to verified teachers."""

    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_teacher:
            raise PermissionDenied(_("This page is for teachers only."))
        if not request.user.teacher_profile.is_verified_teacher:
            raise PermissionDenied(_("Your teacher account is pending verification."))
        return view_func(request, *args, **kwargs)

    return wrapper


def staff_required(view_func):
    """Allows access only to staff users."""

    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied(_("Staff access only."))
        return view_func(request, *args, **kwargs)

    return wrapper


def anonymous_required(redirect_url="dashboard"):
    """
    Redirects authenticated users away from guest-only pages
    e.g. login, signup pages.
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.user.is_authenticated:
                from django.shortcuts import redirect

                return redirect(redirect_url)
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator
