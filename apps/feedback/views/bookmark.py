from collections import defaultdict

from django.contrib.contenttypes.models import ContentType
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Case, CharField, OuterRef, Q, Subquery, Value, When
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import TemplateView

from apps.authentication.mixins import StudentRequiredMixin
from apps.content.models import Resource, VideoResource

from ..models import Bookmark
from ..services.bookmark import BookmarkFilterExtractor, BookmarkToggleService

BOOKMARKS_PER_PAGE = 12

# class BookmarkResourceView(LoginRequiredMixin, View):
#     """
#     Creates or removes a bookmark for any active Resource.

#     - GET  → returns current bookmark status
#     - POST → toggles the bookmark (creates if missing, deletes if exists)

#     Business Rules:
#     - User must be authenticated and have the student role.
#     - Resource must exist and be active.
#     """

#     http_method_names = ["get", "post"]

#     def dispatch(self, request, *args, **kwargs):
#         if (
#             request.user.is_authenticated
#             and getattr(request.user, "role", None) != "student"
#         ):
#             return JsonResponse(
#                 {"error": _("Only students can manage bookmarks.")},
#                 status=403,
#             )
#         return super().dispatch(request, *args, **kwargs)

#     def get_resource(self, pk):
#         """
#         Fetch any active resource by pk.
#         No restriction on resource_type — bookmarking is type-agnostic.
#         """
#         return (
#             Resource.objects.select_related(
#                 "course__grade_subject__grade__level",
#                 "grade_subject",
#             )
#             .filter(pk=pk, is_active=True)
#             .first()
#         )

#     def get(self, request, pk):
#         resource = self.get_resource(pk)
#         if not resource:
#             return JsonResponse(
#                 {"error": _("Resource not found or not accessible.")}, status=404
#             )

#         ct = ContentType.objects.get_for_model(Resource)
#         is_bookmarked = Bookmark.objects.filter(
#             student=request.user,
#             content_type=ct,
#             object_id=resource.pk,
#             active=True,
#         ).exists()

#         return JsonResponse(
#             {
#                 "is_bookmarked": is_bookmarked,
#                 "resource_id": str(resource.pk),
#                 "resource_type": resource.resource_type,
#             }
#         )

#     def post(self, request, pk):
#         resource = self.get_resource(pk)
#         if not resource:
#             return JsonResponse(
#                 {"error": _("Resource not found or not accessible.")}, status=404
#             )

#         ct = ContentType.objects.get_for_model(Resource)

#         bookmark, created = Bookmark.objects.get_or_create(
#             student=request.user,
#             content_type=ct,
#             object_id=resource.pk,
#             defaults={"active": True},
#         )

#         if not created:
#             bookmark.active = not bookmark.active
#             bookmark.save(update_fields=["active", "updated_at"])

#         return JsonResponse(
#             {
#                 "bookmarked": bookmark.active,
#                 "message": (
#                     _("Bookmark added.") if bookmark.active else _("Bookmark removed.")
#                 ),
#                 "resource_id": str(resource.pk),
#             },
#             status=200,
#         )


class BookmarkResourceView(StudentRequiredMixin, View):
    """
    Creates or removes a bookmark for any active Resource.
    POST accepts an optional ``note`` field — saved on creation or reactivation.
    """

    http_method_names = ["get", "post"]

    def __init__(self, service: BookmarkToggleService | None = None, **kwargs):
        super().__init__(**kwargs)
        self.service = service or BookmarkToggleService()

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
        bookmark = Bookmark.objects.filter(
            student=request.user,
            content_type=ct,
            object_id=resource.pk,
            active=True,
        ).first()

        return JsonResponse(
            {
                "is_bookmarked": bookmark is not None,
                "note": bookmark.note if bookmark else "",
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

        note = request.POST.get("note", "").strip()
        action = request.POST.get("action", "toggle")  # 'save' | 'remove' | 'toggle'
        ct = ContentType.objects.get_for_model(Resource)

        if action == "save":
            # Always ensure active; update note if already exists
            bookmark, is_active = self.service.save(
                student=request.user,
                content_type=ct,
                object_id=resource.pk,
                note=note,
            )
        elif action == "remove":
            bookmark, is_active = self.service.remove(
                student=request.user,
                content_type=ct,
                object_id=resource.pk,
            )
        else:
            # Legacy toggle fallback (e.g. direct API callers)
            bookmark, is_active = self.service.toggle(
                student=request.user,
                content_type=ct,
                object_id=resource.pk,
                note=note,
            )

        return JsonResponse(
            {
                "bookmarked": is_active,
                "note": bookmark.note,
                "message": (
                    _("Bookmark added.") if is_active else _("Bookmark removed.")
                ),
                "resource_id": str(resource.pk),
            },
            status=200,
        )


# class BookmarkVideoView(LoginRequiredMixin, View):

#     http_method_names = ["get", "post"]

#     def dispatch(self, request, *args, **kwargs):
#         if (
#             request.user.is_authenticated
#             and getattr(request.user, "role", None) != "student"
#         ):
#             return JsonResponse(
#                 {"error": _("Only students can manage bookmarks.")},
#                 status=403,
#             )
#         return super().dispatch(request, *args, **kwargs)

#     def get_video(self, pk):
#         return VideoResource.objects.filter(pk=pk, is_active=True).first()

#     def get(self, request, pk):
#         video = self.get_video(pk)
#         if not video:
#             return JsonResponse({"error": _("Video not found.")}, status=404)

#         ct = ContentType.objects.get_for_model(VideoResource)
#         is_bookmarked = Bookmark.objects.filter(
#             student=request.user,
#             content_type=ct,
#             object_id=video.pk,
#             active=True,
#         ).exists()

#         return JsonResponse(
#             {
#                 "is_bookmarked": is_bookmarked,
#                 "video_id": str(video.pk),
#             }
#         )

#     def post(self, request, pk):
#         video = self.get_video(pk)
#         if not video:
#             return JsonResponse({"error": _("Video not found.")}, status=404)

#         ct = ContentType.objects.get_for_model(VideoResource)

#         bookmark, created = Bookmark.objects.get_or_create(
#             student=request.user,
#             content_type=ct,
#             object_id=video.pk,
#             defaults={"active": True},
#         )

#         if not created:
#             bookmark.active = not bookmark.active
#             bookmark.save(update_fields=["active", "updated_at"])

#         return JsonResponse(
#             {
#                 "bookmarked": bookmark.active,
#                 "message": (
#                     _("Bookmark added.") if bookmark.active else _("Bookmark removed.")
#                 ),
#                 "video_id": str(video.pk),
#             }
#         )


class BookmarkVideoView(StudentRequiredMixin, View):
    """
    Creates or removes a bookmark for any active VideoResource.
    POST accepts an optional ``note`` field — saved on creation or reactivation.
    """

    http_method_names = ["get", "post"]

    def __init__(self, service: BookmarkToggleService | None = None, **kwargs):
        super().__init__(**kwargs)
        self.service = service or BookmarkToggleService()

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

    def get_video(self, pk):
        return VideoResource.objects.filter(pk=pk, is_active=True).first()

    def get(self, request, pk):
        video = self.get_video(pk)
        if not video:
            return JsonResponse({"error": _("Video not found.")}, status=404)

        ct = ContentType.objects.get_for_model(VideoResource)
        bookmark = Bookmark.objects.filter(
            student=request.user,
            content_type=ct,
            object_id=video.pk,
            active=True,
        ).first()

        return JsonResponse(
            {
                "is_bookmarked": bookmark is not None,
                "note": bookmark.note if bookmark else "",
                "video_id": str(video.pk),
            }
        )

    def post(self, request, pk):
        video = self.get_video(pk)
        if not video:
            return JsonResponse({"error": _("Video not found.")}, status=404)

        note = request.POST.get("note", "").strip()
        action = request.POST.get("action", "toggle")  # 'save' | 'remove' | 'toggle'
        ct = ContentType.objects.get_for_model(VideoResource)

        if action == "save":
            # Always ensure active; update note if already exists
            bookmark, is_active = self.service.save(
                student=request.user,
                content_type=ct,
                object_id=video.pk,
                note=note,
            )
        elif action == "remove":
            bookmark, is_active = self.service.remove(
                student=request.user,
                content_type=ct,
                object_id=video.pk,
            )
        else:
            # Legacy toggle fallback (e.g. direct API callers)
            bookmark, is_active = self.service.toggle(
                student=request.user,
                content_type=ct,
                object_id=video.pk,
                note=note,
            )

        return JsonResponse(
            {
                "bookmarked": is_active,
                "note": bookmark.note if bookmark else "",
                "message": (
                    _("Bookmark added.") if is_active else _("Bookmark removed.")
                ),
                "video_id": str(video.pk),
            },
            status=200,
        )

    # def post(self, request, pk):
    #     video = self.get_video(pk)
    #     if not video:
    #         return JsonResponse({"error": _("Video not found.")}, status=404)

    #     note = request.POST.get("note", "").strip()
    #     ct = ContentType.objects.get_for_model(VideoResource)

    #     bookmark, is_active = self.service.toggle(
    #         student=request.user,
    #         content_type=ct,
    #         object_id=video.pk,
    #         note=note,
    #     )

    #     return JsonResponse(
    #         {
    #             "bookmarked": is_active,
    #             "note": bookmark.note,
    #             "message": (
    #                 _("Bookmark added.") if is_active else _("Bookmark removed.")
    #             ),
    #             "video_id": str(video.pk),
    #         },
    #         status=200,
    #     )


# class StudentBookmarkListView(LoginRequiredMixin, TemplateView):
#     """
#     Display the student's active bookmarks grouped by content type
#     and ordered by most recent first.
#     """

#     template_name = "apps/feedback/bookmarks/list.html"

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         user = self.request.user

#         bookmarks = (
#             Bookmark.objects.filter(student=user, active=True)
#             .select_related("content_type")
#             .order_by("-updated_at")
#         )

#         grouped_bookmarks = defaultdict(list)
#         for bookmark in bookmarks:
#             grouped_bookmarks[bookmark.target_type].append(bookmark)

#         ordered_types = Bookmark.ALLOWED_MODELS
#         grouped_bookmarks = {
#             content_type: grouped_bookmarks.get(content_type, [])
#             for content_type in ordered_types
#             if grouped_bookmarks.get(content_type)
#         }

#         context.update(
#             {
#                 "bookmarks": bookmarks,
#                 "grouped_bookmarks": grouped_bookmarks,
#                 "total_count": bookmarks.count(),
#             }
#         )
#         return context


class StudentBookmarkListView(StudentRequiredMixin, TemplateView):
    """
    Display the student's active bookmarks grouped by content type,
    with optional search (note) and content-type filter.
    """

    template_name = "apps/feedback/bookmarks/list.html"
    paginate_by = BOOKMARKS_PER_PAGE

    def __init__(
        self, filter_extractor: BookmarkFilterExtractor | None = None, **kwargs
    ):
        super().__init__(**kwargs)
        self.filter_extractor = filter_extractor or BookmarkFilterExtractor()

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self._filters = self.filter_extractor.extract(request, Bookmark.ALLOWED_MODELS)

    def get_queryset(self, user):
        filters = self._filters

        # Resolved once — two DB hits but cached by Django's CT framework
        resource_ct = ContentType.objects.get_for_model(Resource)
        video_ct = ContentType.objects.get_for_model(VideoResource)

        qs = (
            Bookmark.objects.filter(student=user, active=True)
            .select_related("content_type")
            .order_by("-updated_at")
            # ── Annotate with the related object's title ──────────────
            .annotate(
                obj_title=Case(
                    When(
                        content_type=resource_ct,
                        then=Subquery(
                            Resource.objects.filter(pk=OuterRef("object_id")).values(
                                "title"
                            )[:1]
                        ),
                    ),
                    When(
                        content_type=video_ct,
                        then=Subquery(
                            VideoResource.objects.filter(
                                pk=OuterRef("object_id")
                            ).values("title")[:1]
                        ),
                    ),
                    default=Value(""),
                    output_field=CharField(),
                )
            )
        )

        # ── Search: note OR title ─────────────────────────────────────
        if filters.q:
            qs = qs.filter(
                Q(note__icontains=filters.q) | Q(obj_title__icontains=filters.q)
            )

        # ── Filter: content_type model name ───────────────────────────
        if filters.content_type:
            qs = qs.filter(content_type__model=filters.content_type)

        return qs

    def paginate_queryset(self, qs):
        """
        Returns (page_obj, paginator).
        Clamps out-of-range page numbers instead of raising 404 —
        avoids broken pages if the last bookmark on page N is deleted.
        """
        paginator = Paginator(qs, self.paginate_by)
        raw_page = self.request.GET.get("page", 1)

        try:
            page_obj = paginator.page(raw_page)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        return page_obj, paginator

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        filters = self._filters

        qs = self.get_queryset(user)
        total_count = qs.count()
        page_obj, paginator = self.paginate_queryset(qs)

        # ── Grouping (respects active filters) ────────────────────
        grouped_bookmarks = defaultdict(list)
        for bookmark in page_obj.object_list:
            grouped_bookmarks[bookmark.target_type].append(bookmark)

        grouped_bookmarks = {
            ct: grouped_bookmarks[ct]
            for ct in Bookmark.ALLOWED_MODELS
            if grouped_bookmarks.get(ct)
        }

        context.update(
            {
                "grouped_bookmarks": grouped_bookmarks,
                "page_obj": page_obj,
                "paginator": paginator,
                "is_paginated": paginator.num_pages > 1,
                "total_count": total_count,
                # filters — fed back to template
                "filter_q": filters.q,
                "filter_type": filters.content_type,
                "querystring": filters.querystring,
                "allowed_types": Bookmark.ALLOWED_MODELS,
            }
        )
        return context
