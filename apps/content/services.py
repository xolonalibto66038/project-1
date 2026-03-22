from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from apps.progress.models import ContentProgress


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
