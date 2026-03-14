# recommendations/views.py

from django.shortcuts import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import RecommendedItemSerializer
from .service import RecommendationService

service = RecommendationService()

# ── Shared select_related paths ────────────────────────────────────────────────
# These mirror the traversal done by the extractors so the FK chain is
# already in memory when feature extraction runs — no extra queries.

_RESOURCE_SELECT_RELATED = [
    "course__chapter__grade_subject__grade__level",
    "course__chapter__grade_subject__subject",
    "course__chapter__grade_subject__specialty",
    "course__grade_subject__grade__level",
    "course__grade_subject__subject",
    "course__grade_subject__specialty",
    "grade_subject__grade__level",
    "grade_subject__subject",
    "grade_subject__specialty",
]

_COURSE_SELECT_RELATED = [
    "chapter__grade_subject__grade__level",
    "chapter__grade_subject__subject",
    "chapter__grade_subject__specialty",
    "grade_subject__grade__level",
    "grade_subject__subject",
    "grade_subject__specialty",
]


# ── Query param helpers ────────────────────────────────────────────────────────


def _get_limit(request, default: int = 6, max_limit: int = 20) -> int:
    """
    Reads ?limit= from the request, clamps it to [1, max_limit].
    Falls back to *default* on missing or invalid values.
    """
    try:
        limit = int(request.query_params.get("limit", default))
        return max(1, min(limit, max_limit))
    except (TypeError, ValueError):
        return default


# ── Views ──────────────────────────────────────────────────────────────────────


class SimilarResourcesView(APIView):
    """
    GET /api/recommendations/resources/<uuid:pk>/similar/

    Returns resources (and courses) similar to the given resource.
    Ordered by descending similarity score.

    Query params:
        limit   int   Number of results (default 6, max 20)

    Permissions:
        - Free resources: open to anyone.
        - Non-free resources: authenticated users only.
          (The service always runs; the permission check is on the *source*
          resource, not the results — results inherit the same access level.)
    """

    permission_classes = [AllowAny]

    def get(self, request, pk):
        from apps.content.models import Resource

        resource = get_object_or_404(
            Resource.objects.select_related(*_RESOURCE_SELECT_RELATED),
            pk=pk,
            is_active=True,
        )

        # Non-free source resources require authentication
        if not resource.is_free and not request.user.is_authenticated:
            return Response(
                {
                    "detail": "Authentication required to view recommendations for this resource."
                },
                status=401,
            )

        limit = _get_limit(request)
        results = service.similar_to(resource, limit=limit)

        return Response(
            {
                "count": len(results),
                "results": RecommendedItemSerializer(
                    results, many=True, context={"request": request}
                ).data,
            }
        )


class SimilarCoursesView(APIView):
    """
    GET /api/recommendations/courses/<uuid:pk>/similar/

    Returns courses (and resources) similar to the given course.

    Query params:
        limit   int   Number of results (default 6, max 20)
    """

    permission_classes = [AllowAny]

    def get(self, request, pk):
        from apps.content.models import Course

        course = get_object_or_404(
            Course.objects.select_related(*_COURSE_SELECT_RELATED),
            pk=pk,
            is_active=True,
        )

        limit = _get_limit(request)
        results = service.similar_to(course, limit=limit)

        return Response(
            {
                "count": len(results),
                "results": RecommendedItemSerializer(
                    results, many=True, context={"request": request}
                ).data,
            }
        )


class GradeSubjectResourcesView(APIView):
    """
    GET /api/recommendations/grade-subjects/<uuid:pk>/resources/

    Returns popular resources within a GradeSubject.
    Used on subject landing pages — no reference item required.

    Query params:
        limit   int   Number of results (default 8, max 20)
    """

    permission_classes = [AllowAny]

    def get(self, request, pk):
        from apps.curriculum.models import GradeSubject

        grade_subject = get_object_or_404(
            GradeSubject.objects.select_related(
                "grade__level",
                "subject",
                "specialty",
            ),
            pk=pk,
            is_active=True,
        )

        limit = _get_limit(request, default=8)
        results = service.similar_resources_in_grade_subject(grade_subject, limit=limit)

        return Response(
            {
                "count": len(results),
                "results": RecommendedItemSerializer(
                    results, many=True, context={"request": request}
                ).data,
            }
        )


class CourseResourcesView(APIView):
    """
    GET /api/recommendations/courses/<uuid:pk>/resources/

    Returns resources within a Course, ordered by curriculum position.
    Used as a "more from this course" widget on course detail pages.

    Query params:
        limit   int   Number of results (default 8, max 20)
    """

    permission_classes = [AllowAny]

    def get(self, request, pk):
        from apps.content.models import Course

        course = get_object_or_404(
            Course.objects.select_related(*_COURSE_SELECT_RELATED),
            pk=pk,
            is_active=True,
        )

        limit = _get_limit(request, default=8)
        results = service.similar_resources_in_course(course, limit=limit)

        return Response(
            {
                "count": len(results),
                "results": RecommendedItemSerializer(
                    results, many=True, context={"request": request}
                ).data,
            }
        )
