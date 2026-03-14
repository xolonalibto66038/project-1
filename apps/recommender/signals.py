# recommendations/signals.py

"""
Keeps ItemFeatureVector rows in sync with content model changes.

Wired up in RecommendationsConfig.ready():

    # recommendations/apps.py
    class RecommendationsConfig(AppConfig):
        name = "recommendations"

        def ready(self):
            import recommendations.signals    # noqa: F401
            import recommendations.extractors # noqa: F401  ← registers @register decorators
"""

import logging

from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import ItemFeatureVector
from .registry import get_features

logger = logging.getLogger(__name__)


# ── Core upsert / delete ───────────────────────────────────────────────────────


def _upsert_vector(instance) -> bool:
    """
    Extract features for *instance* and upsert its ItemFeatureVector row.

    Returns True on success, False when skipped (no extractor or bad data).
    Never raises — recommendation failures must never crash a content save.
    """
    features = get_features(instance)  # registry handles exceptions internally

    if features is None:
        # No extractor registered for this model — nothing to do.
        return False

    ct = ContentType.objects.get_for_model(instance)

    try:
        ItemFeatureVector.objects.update_or_create(
            content_type=ct,
            object_id=instance.pk,
            defaults={
                "level_id": features.get("level_id"),
                "grade_id": features.get("grade_id"),
                "subject_id": features.get("subject_id"),
                "specialty_id": features.get("specialty_id"),
                "course_id": features.get("course_id"),
                "item_type": features.get("item_type", ""),
                "difficulty": features.get("difficulty"),
                "term": features.get("term"),
            },
        )
    except Exception:
        logger.exception(
            "signals._upsert_vector: failed for %s pk=%s.",
            instance.__class__.__name__,
            instance.pk,
        )
        return False

    return True


def _delete_vector(instance) -> None:
    """
    Remove the ItemFeatureVector row for *instance* if it exists.
    Never raises.
    """
    ct = ContentType.objects.get_for_model(instance)
    try:
        ItemFeatureVector.objects.filter(
            content_type=ct,
            object_id=instance.pk,
        ).delete()
    except Exception:
        logger.exception(
            "signals._delete_vector: failed for %s pk=%s.",
            instance.__class__.__name__,
            instance.pk,
        )


# ── Resource signals ───────────────────────────────────────────────────────────


@receiver(post_save, sender="content.Resource")
def on_resource_save(sender, instance, **kwargs):
    """
    Rebuild the feature vector whenever a Resource is created or updated.

    post_save is used (not pre_save) so all FK relations are already
    committed and can be traversed without extra queries.
    """
    _upsert_vector(instance)


@receiver(post_delete, sender="content.Resource")
def on_resource_delete(sender, instance, **kwargs):
    _delete_vector(instance)


# ── Course signals ─────────────────────────────────────────────────────────────


@receiver(post_save, sender="content.Course")
def on_course_save(sender, instance, **kwargs):
    """
    Rebuild the feature vector for the Course, then cascade to all its
    Resources — because a Resource's effective level/grade/subject is
    derived from its Course, so a Course reparent makes every child stale.
    """
    _upsert_vector(instance)
    _cascade_course_resources(instance)


@receiver(post_delete, sender="content.Course")
def on_course_delete(sender, instance, **kwargs):
    _delete_vector(instance)
    # Child Resource rows are deleted by CASCADE on the DB FK, which fires
    # their own post_delete signals — no manual cleanup needed here.


# ── Chapter signals ────────────────────────────────────────────────────────────
#
# When a Chapter is reparented (grade_subject changes) or its term changes,
# every Course → Resource beneath it becomes stale.
#


@receiver(post_save, sender="content.Chapter")
def on_chapter_save(sender, instance, **kwargs):
    """
    Cascade through Chapter → Courses → Resources when a Chapter changes.
    """
    _cascade_chapter_courses(instance)


# ── Cascade helpers ────────────────────────────────────────────────────────────


def _cascade_course_resources(course) -> None:
    """
    Rebuild ItemFeatureVector for every active Resource that belongs to *course*.

    Uses a single select_related query to avoid N+1 traversals during
    feature extraction (extractors walk up to level via grade_subject).
    """
    from apps.content.models import Resource  # local import — avoids circular deps

    resources = Resource.objects.filter(course=course).select_related(
        "course__chapter__grade_subject__grade__level",
        "course__chapter__grade_subject__subject",
        "course__chapter__grade_subject__specialty",
        "course__grade_subject__grade__level",
        "course__grade_subject__subject",
        "course__grade_subject__specialty",
    )

    for resource in resources:
        _upsert_vector(resource)


def _cascade_chapter_courses(chapter) -> None:
    """
    Rebuild ItemFeatureVector for every Course that belongs to *chapter*,
    then cascade further to their Resources.
    """
    from apps.content.models import Course  # local import — avoids circular deps

    courses = Course.objects.filter(chapter=chapter).select_related(
        "chapter__grade_subject__grade__level",
        "chapter__grade_subject__subject",
        "chapter__grade_subject__specialty",
    )

    for course in courses:
        _upsert_vector(course)
        _cascade_course_resources(course)
