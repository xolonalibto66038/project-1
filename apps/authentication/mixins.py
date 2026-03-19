# apps/authentication/mixins.py

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _


class StudentRequiredMixin(LoginRequiredMixin):
    """Allows access only to authenticated students."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.is_student:
            raise PermissionDenied(_("This page is for students only."))
        return super().dispatch(request, *args, **kwargs)


class TeacherRequiredMixin(LoginRequiredMixin):
    """Allows access only to authenticated teachers."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.is_teacher:
            raise PermissionDenied(_("This page is for teachers only."))
        return super().dispatch(request, *args, **kwargs)


# class VerifiedTeacherRequiredMixin(TeacherRequiredMixin):
#     """Allows access only to verified teachers."""


#     def dispatch(self, request, *args, **kwargs):
#         response = super().dispatch(request, *args, **kwargs)
#         # super() already checked is_teacher
#         if not request.user.teacher_profile.is_verified_teacher:
#             raise PermissionDenied(_("Your teacher account is pending verification."))
#         return response
class VerifiedTeacherRequiredMixin(TeacherRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        # Use select_related to avoid extra query, or cache on request
        teacher_profile = getattr(request.user, "_cached_teacher_profile", None)
        if teacher_profile is None:
            teacher_profile = request.user.teacher_profile
            request.user._cached_teacher_profile = teacher_profile
        if not teacher_profile.is_verified_teacher:
            raise PermissionDenied(_("Your teacher account is pending verification."))
        return response


class StaffRequiredMixin(LoginRequiredMixin):
    """Allows access only to staff/admin users."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.is_staff:
            raise PermissionDenied(_("Staff access only."))
        return super().dispatch(request, *args, **kwargs)


class OwnerRequiredMixin(LoginRequiredMixin):
    """
    Ensures the requesting user owns the object.
    The view must implement get_object().
    Override get_owner() if the owner field is not 'author'.
    """

    owner_field = "author"

    def get_owner(self, obj):
        return getattr(obj, self.owner_field, None)

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, *args, **kwargs):
        obj = super().get_object(*args, **kwargs)
        owner = self.get_owner(obj)
        if owner != self.request.user and not self.request.user.is_staff:
            raise PermissionDenied(_("You do not have permission to access this."))
        return obj
