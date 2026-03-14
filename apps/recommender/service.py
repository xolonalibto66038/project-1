# recommendations/service.py

import logging

from django.contrib.contenttypes.models import ContentType

from .engine import rank_candidates
from .models import ItemFeatureVector
from .registry import get_features

logger = logging.getLogger(__name__)


class RecommendationService:
    """
    Phase 1: Content-based recommendation service.

    Public interface:
        - similar_to(instance, limit, min_score)
            → list of similar instances of any registered model

        - similar_resources_in_grade_subject(grade_subject, exclude_ids, limit)
            → resources within a grade/subject landing page

        - similar_resources_in_course(course, exclude_ids, limit)
            → resources within a course detail page
    """

    # ── Public API ─────────────────────────────────────────────────────────────

    def similar_to(self, instance, limit: int = 6, min_score: float = 0.2):
        """
        Returns instances similar to `instance`.
        Works for any model that has a registered extractor (Resource, Course).

        Strategy:
          1. Prefer the precomputed ItemFeatureVector row (fast, no traversal).
          2. Fall back to live feature extraction if the vector is missing
             (e.g. signal hasn't fired yet after a fresh migration).
          3. Pre-filter candidates in the DB to avoid scoring the entire table.
          4. Bulk-resolve model instances grouped by content type (1 query/type).
          5. Score and rank via the engine.
        """
        ct = ContentType.objects.get_for_model(instance)

        source_features = self._get_source_features(ct, instance)
        if source_features is None:
            return []

        candidate_vectors = self._get_candidate_vectors(
            source_features=source_features,
            exclude_id=instance.pk,
        )
        if not candidate_vectors:
            return []

        candidates_with_features = self._resolve_instances(candidate_vectors)
        if not candidates_with_features:
            return []

        return [
            inst
            for _, inst in rank_candidates(
                source_features, candidates_with_features, limit, min_score
            )
        ]

    def similar_resources_in_grade_subject(
        self,
        grade_subject,
        exclude_ids=None,
        limit: int = 8,
    ):
        """
        Returns active resources within a GradeSubject, ordered by popularity.
        Used on subject landing pages where there is no single reference item.

        Filters to the correct specialty automatically:
          - If grade_subject has a specialty, only that specialty's resources.
          - If no specialty (applies to all), returns all resources for the pair.

        Phase 2 note: replace order_by with a collaborative-filter score.
        """
        from apps.content.models import Resource

        qs = (
            Resource.objects.filter(
                grade_subject=grade_subject,
                is_active=True,
            )
            .select_related(
                "grade_subject__grade__level",
                "grade_subject__subject",
                "grade_subject__specialty",
            )
            .order_by("-download_count", "-view_count")
        )

        if exclude_ids:
            qs = qs.exclude(pk__in=exclude_ids)

        return list(qs[:limit])

    def similar_resources_in_course(
        self,
        course,
        exclude_ids=None,
        limit: int = 8,
    ):
        """
        Returns active resources within a Course, ordered by curriculum position.
        Used on course detail pages as a "more from this course" widget.
        """
        from apps.content.models import Resource

        qs = (
            Resource.objects.filter(
                course=course,
                is_active=True,
            )
            .select_related("course")
            .order_by("order")
        )

        if exclude_ids:
            qs = qs.exclude(pk__in=exclude_ids)

        return list(qs[:limit])

    # ── Private helpers ────────────────────────────────────────────────────────

    def _get_source_features(self, ct, instance) -> dict | None:
        """
        Returns the feature dict for *instance*.

        Prefers the precomputed vector row; falls back to live extraction.
        Returns None if neither is available (unregistered model or broken FK).
        """
        vector = self._get_vector(ct, instance.pk)

        if vector is not None:
            return self._vector_to_dict(vector)

        logger.warning(
            "RecommendationService: no ItemFeatureVector for %s pk=%s — "
            "falling back to live extraction.",
            ct.model,
            instance.pk,
        )
        features = get_features(instance)

        if features is None:
            logger.error(
                "RecommendationService: live extraction also failed for %s pk=%s. "
                "No extractor registered or extractor raised. Returning empty.",
                ct.model,
                instance.pk,
            )

        return features

    def _get_vector(self, ct, object_id) -> ItemFeatureVector | None:
        try:
            return ItemFeatureVector.objects.get(
                content_type=ct,
                object_id=object_id,
            )
        except ItemFeatureVector.DoesNotExist:
            return None

    def _vector_to_dict(self, vector: ItemFeatureVector) -> dict:
        """
        Converts an ItemFeatureVector row into the feature dict
        consumed by the engine. Keys must match FEATURE_KEYS in registry.py.
        """
        return {
            "level_id": vector.level_id,
            "grade_id": vector.grade_id,
            "subject_id": vector.subject_id,
            "specialty_id": vector.specialty_id,
            "course_id": vector.course_id,
            "item_type": vector.item_type,
            "difficulty": vector.difficulty,
            "term": vector.term,
        }

    def _get_candidate_vectors(
        self,
        source_features: dict,
        exclude_id,
    ) -> list[ItemFeatureVector]:
        """
        Pre-filters ItemFeatureVector rows in the DB before scoring.

        Filter strategy (most → least selective):
          1. Exclude the source item itself.
          2. level_id   — hard constraint: never cross-level (mandatory).
          3. grade_id   — hard constraint: never cross-grade (mandatory).
          4. subject_id — narrows to the same subject (strong signal).
          5. specialty_id — applied only when source has a specialty,
             broadened to include NULL rows (items that apply to all).

        Intentionally does NOT filter by course_id or term here — those
        are scoring signals, not pre-filters, so partial matches still
        surface from the engine.
        """
        qs = ItemFeatureVector.objects.exclude(object_id=exclude_id)

        level_id = source_features.get("level_id")
        if level_id:
            qs = qs.filter(level_id=level_id)

        grade_id = source_features.get("grade_id")
        if grade_id:
            qs = qs.filter(grade_id=grade_id)

        subject_id = source_features.get("subject_id")
        if subject_id:
            qs = qs.filter(subject_id=subject_id)

        specialty_id = source_features.get("specialty_id")
        if specialty_id:
            # Include items for this specialty AND items with no specialty
            # (those apply to all filières and are always relevant)
            from django.db.models import Q

            qs = qs.filter(Q(specialty_id=specialty_id) | Q(specialty_id__isnull=True))
        # If source has no specialty (NULL), all specialties are candidates —
        # no filter needed; the engine will score specialty matches higher.

        return list(qs)

    def _resolve_instances(
        self,
        vectors: list[ItemFeatureVector],
    ) -> list[tuple[any, dict]]:
        """
        Bulk-fetches model instances from the DB grouped by content type.
        Emits exactly one SELECT per distinct content type — not one per vector.

        Silently drops vectors whose instance no longer exists in the DB
        (deleted between the vector fetch and this query).
        """
        # Group vectors by content type to batch the queries
        by_ct: dict[int, list[ItemFeatureVector]] = {}
        for v in vectors:
            by_ct.setdefault(v.content_type_id, []).append(v)

        result = []
        for ct_id, ct_vectors in by_ct.items():
            ct = ContentType.objects.get_for_id(ct_id)
            model_class = ct.model_class()
            ids = [v.object_id for v in ct_vectors]

            instances = {
                str(inst.pk): inst for inst in model_class.objects.filter(pk__in=ids)
            }

            for vector in ct_vectors:
                inst = instances.get(str(vector.object_id))
                if inst is None:
                    # Stale vector — instance was deleted without firing post_delete
                    logger.debug(
                        "RecommendationService: stale vector for %s pk=%s — skipping.",
                        ct.model,
                        vector.object_id,
                    )
                    continue
                result.append((inst, self._vector_to_dict(vector)))

        return result
