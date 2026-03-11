from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from apps.progress.models import ContentProgress

from .selectors import get_or_create_course_progress


def record_course_visit(student, course):
    """
    Creates or updates ContentProgress for a student visiting a course.
    Idempotent — safe to call on every GET.
    Returns the ContentProgress instance.
    """
    progress, created = get_or_create_course_progress(student, course)

    if not created:
        # bump first_viewed_at only on first visit; just return on repeat
        pass

    return progress


def _track_student_first_view(user, resource):
    """
    Creates a ContentProgress record on first visit.
    Idempotent — get_or_create ensures no duplicates.
    Does NOT mark as completed — that's a separate action.
    """
    content_type = ContentType.objects.get_for_model(resource)

    ContentProgress.objects.get_or_create(
        student=user,
        content_type=content_type,
        object_id=resource.pk,
        defaults={
            "is_completed": False,
            "first_viewed_at": timezone.now(),
        },
    )
