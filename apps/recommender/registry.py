# recommendations/registry.py

import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)

# ── Expected feature contract ──────────────────────────────────────────────────
#
# Every registered extractor must return a dict with exactly these keys.
# Values may be None when the field is not applicable to the item.
#
FEATURE_KEYS: frozenset[str] = frozenset(
    {
        "level_id",
        "grade_id",
        "subject_id",
        "specialty_id",
        "course_id",
        "item_type",
        "difficulty",
        "term",
    }
)

# ── Internal registry ──────────────────────────────────────────────────────────
# model_label (lowercase class name) → extractor callable
_REGISTRY: dict[str, Callable] = {}


# ── Public API ─────────────────────────────────────────────────────────────────


def register(model_label: str):
    """
    Decorator to register a feature extractor for a curriculum model.

    The decorated function must accept a single model instance and return
    a dict containing exactly the keys defined in FEATURE_KEYS.

    Usage:
        @register("resource")
        def extract_resource(instance) -> dict:
            return {
                "level_id":    instance.grade_subject.grade.level.pk,
                "grade_id":    instance.grade_subject.grade.pk,
                "subject_id":  instance.grade_subject.subject.pk,
                "specialty_id": instance.grade_subject.specialty_id,
                "course_id":   instance.course_id,
                "item_type":   instance.resource_type,
                "difficulty":  instance.difficulty,
                "term":        instance.term or None,
            }
    """

    def decorator(fn: Callable) -> Callable:
        label = model_label.lower()

        if label in _REGISTRY:
            logger.warning(
                "recommendations.registry: extractor for '%s' is being overwritten "
                "by %s. If this is intentional (e.g. testing), ignore this warning.",
                label,
                fn.__qualname__,
            )

        _REGISTRY[label] = fn
        logger.debug(
            "recommendations.registry: registered extractor '%s' → %s",
            label,
            fn.__qualname__,
        )
        return fn

    return decorator


def get_extractor(model_label: str) -> Optional[Callable]:
    """Returns the registered extractor for *model_label*, or None."""
    return _REGISTRY.get(model_label.lower())


def get_features(instance) -> Optional[dict]:
    """
    Given any model instance, returns its feature dict.

    Returns None — without raising — if:
      - no extractor is registered for this model, or
      - the extractor itself raises an exception (logged as ERROR)

    The None return lets callers decide whether to skip or fall back,
    rather than crashing a content save because of a recommendation issue.
    """
    label = instance.__class__.__name__.lower()
    extractor = get_extractor(label)

    if extractor is None:
        return None

    try:
        features = extractor(instance)
    except Exception:
        logger.exception(
            "recommendations.registry: extractor for '%s' raised an exception "
            "on instance pk=%s. Returning None.",
            label,
            getattr(instance, "pk", "?"),
        )
        return None

    # ── Dev-time validation (skipped in production for performance) ────────────
    if __debug__:
        _validate_features(label, features)

    return features


def registered_models() -> list[str]:
    """Returns a sorted list of all registered model labels. Useful for debugging."""
    return sorted(_REGISTRY.keys())


# ── Internal helpers ───────────────────────────────────────────────────────────


def _validate_features(label: str, features: dict) -> None:
    """
    Warns about missing or unexpected keys in a feature dict.
    Runs only when Python is not started with -O (i.e. __debug__ is True),
    so there is zero overhead in production.
    """
    if not isinstance(features, dict):
        logger.error(
            "recommendations.registry: extractor for '%s' returned %s instead of dict.",
            label,
            type(features).__name__,
        )
        return

    missing = FEATURE_KEYS - features.keys()
    extra = features.keys() - FEATURE_KEYS

    if missing:
        logger.warning(
            "recommendations.registry: extractor for '%s' is missing keys: %s. "
            "Engine will treat them as None.",
            label,
            sorted(missing),
        )
    if extra:
        logger.warning(
            "recommendations.registry: extractor for '%s' returned unexpected keys: %s. "
            "They will be ignored by the engine.",
            label,
            sorted(extra),
        )
