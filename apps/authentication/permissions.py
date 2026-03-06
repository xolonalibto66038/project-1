# apps/authentication/permissions.py

from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _


def can_publish_resource(user):
    """
    Only verified teachers can publish resources.
    Used in views and serializers.
    """
    if not user.is_authenticated:
        return False
    if not user.is_teacher:
        return False
    return user.teacher_profile.is_verified_teacher


def can_rate_content(user):
    """Only students can rate resources."""
    return user.is_authenticated and user.is_student


def can_bookmark_content(user):
    """Only students can bookmark."""
    return user.is_authenticated and user.is_student


def can_edit_resource(user, resource):
    """
    A teacher can edit their own resources.
    Staff can edit any resource.
    """
    if not user.is_authenticated:
        return False
    if user.is_staff:
        return True
    return user.is_teacher and resource.author == user


def assert_can_publish(user):
    """Raises PermissionDenied if user cannot publish. Use in views."""
    if not can_publish_resource(user):
        raise PermissionDenied(
            _('Only verified teachers can publish resources.')
        )


def assert_can_edit_resource(user, resource):
    """Raises PermissionDenied if user cannot edit the resource."""
    if not can_edit_resource(user, resource):
        raise PermissionDenied(
            _('You do not have permission to edit this resource.')
        )