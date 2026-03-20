from collections import defaultdict

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import TemplateView

from apps.content.models import Resource

from ..models import Bookmark


class BookmarkResourceView(LoginRequiredMixin, View):
    """
    Creates or removes a bookmark for any active Resource.

    - GET  → returns current bookmark status
    - POST → toggles the bookmark (creates if missing, deletes if exists)

    Business Rules:
    - User must be authenticated and have the student role.
    - Resource must exist and be active.
    """

    http_method_names = ["get", "post"]

    def dispatch(self, request, *args, **kwargs):
        if (
            request.user.is_authenticated
            and getattr(request.user, "role", None) != "student"
        ):
            return JsonResponse(
                {"error": _("Only students can manage bookmarks.")},
                status=403,
            )
        return super().dispatch(request, *args, **kwargs)

    def get_resource(self, pk):
        """
        Fetch any active resource by pk.
        No restriction on resource_type — bookmarking is type-agnostic.
        """
        return (
            Resource.objects.select_related(
                "course__grade_subject__grade__level",
                "grade_subject",
            )
            .filter(pk=pk, is_active=True)
            .first()
        )

    def get(self, request, pk):
        resource = self.get_resource(pk)
        if not resource:
            return JsonResponse(
                {"error": _("Resource not found or not accessible.")}, status=404
            )

        ct = ContentType.objects.get_for_model(Resource)
        is_bookmarked = Bookmark.objects.filter(
            student=request.user,
            content_type=ct,
            object_id=resource.pk,
            active=True,
        ).exists()

        return JsonResponse(
            {
                "is_bookmarked": is_bookmarked,
                "resource_id": str(resource.pk),
                "resource_type": resource.resource_type,
            }
        )

    def post(self, request, pk):
        resource = self.get_resource(pk)
        if not resource:
            return JsonResponse(
                {"error": _("Resource not found or not accessible.")}, status=404
            )

        ct = ContentType.objects.get_for_model(Resource)

        bookmark, created = Bookmark.objects.get_or_create(
            student=request.user,
            content_type=ct,
            object_id=resource.pk,
            defaults={"active": True},
        )

        if not created:
            bookmark.active = not bookmark.active
            bookmark.save(update_fields=["active", "updated_at"])

        return JsonResponse(
            {
                "bookmarked": bookmark.active,
                "message": (
                    _("Bookmark added.") if bookmark.active else _("Bookmark removed.")
                ),
                "resource_id": str(resource.pk),
            },
            status=200,
        )


class StudentBookmarkListView(LoginRequiredMixin, TemplateView):
    """
    Display the student's active bookmarks grouped by content type
    and ordered by most recent first.
    """

    template_name = "apps/feedback/bookmarks/list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        bookmarks = (
            Bookmark.objects.filter(student=user, active=True)
            .select_related("content_type")
            .order_by("-updated_at")
        )

        grouped_bookmarks = defaultdict(list)
        for bookmark in bookmarks:
            grouped_bookmarks[bookmark.target_type].append(bookmark)

        ordered_types = Bookmark.ALLOWED_MODELS
        grouped_bookmarks = {
            content_type: grouped_bookmarks.get(content_type, [])
            for content_type in ordered_types
            if grouped_bookmarks.get(content_type)
        }

        context.update(
            {
                "bookmarks": bookmarks,
                "grouped_bookmarks": grouped_bookmarks,
                "total_count": bookmarks.count(),
            }
        )
        return context
