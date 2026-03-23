import logging
from functools import wraps

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext_lazy as _

from apps.accounts.choices import UserRole
from apps.accounts.models import CustomUser

logger = logging.getLogger(__name__)


def teacher_level_required(view_func):
    """
    Ensures the authenticated student belongs to the same education level
    as the subject the teacher is teaching.

    Guard: student.profile.grade.level == teacher.subject.level

    Fails gracefully with a warning message and redirects to the
    available-teachers page for that subject when the check fails.

    Must be placed AFTER @login_required and @student_required so that
    request.user.student_profile is guaranteed to exist.

    Usage:
        @login_required
        @student_required
        @subscription_required
        @teacher_level_required       ← here
        @require_POST
        def select_teacher(request, teacher_id):
            ...
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        teacher_id = kwargs.get("teacher_id") or args[0]

        teacher = get_object_or_404(
            CustomUser,
            id=teacher_id,
            role=UserRole.TEACHER,
            is_active=True,
            teacher_profile__is_verified_teacher=True,
        )

        subject = _resolve_teacher_subject(teacher)
        if subject is None:
            logger.warning(
                "teacher_level_required: teacher pk=%s has no subject assigned.",
                teacher.pk,
            )
            messages.warning(
                request,
                _("This teacher has no subject assigned. Please choose another."),
            )
            return redirect("tutoring:student:available-teachers", subject_pk=0)

        student_level = _resolve_student_level(request.user)
        if student_level is None:
            logger.warning(
                "teacher_level_required: student pk=%s has no grade/level assigned.",
                request.user.pk,
            )
            messages.warning(
                request,
                _("Your grade level is not set. Please update your profile."),
            )
            return redirect("users:student:profile")

        if student_level.pk != subject.level.pk:
            logger.info(
                "teacher_level_required: level mismatch — "
                "student level pk=%s, teacher subject level pk=%s.",
                student_level.pk,
                subject.level.pk,
            )
            messages.warning(
                request,
                _(
                    "This teacher teaches a subject for %(level)s, "
                    "which does not match your enrolled level."
                )
                % {"level": subject.level.get_name_display()},
            )
            return redirect(
                "tutoring:student:available-teachers",
                subject_pk=subject.pk,
            )

        return view_func(request, *args, **kwargs)

    return wrapper


# ── Private helpers ───────────────────────────────────────────────────────────


def _resolve_teacher_subject(teacher: object) -> object | None:
    """
    Returns the subject the teacher is assigned to, with level pre-fetched.
    Returns None if the profile or subject is missing.
    """
    try:
        return teacher.teacher_profile.subject.__class__.objects.select_related(
            "level"
        ).get(pk=teacher.teacher_profile.subject.pk)
    except Exception:
        return None


def _resolve_student_level(user: object) -> object | None:
    """
    Returns the Level the student is enrolled in.
    Returns None if profile, grade, or level is missing.
    """
    try:
        return user.student_profile.grade.level
    except Exception:
        return None
