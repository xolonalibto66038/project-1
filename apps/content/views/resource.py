import logging

from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from apps.authentication.mixins import (
    OwnerRequiredMixin,
    TeacherRequiredMixin,
    VerifiedTeacherRequiredMixin,
)
from apps.progress.models import ContentProgress
from apps.recommender.service import RecommendationService
from common.mixins.ratelimit import RatelimitMixin

from ..choices import DifficultyLevel, ResourceType
from ..forms.resource import ResourceCreateForm, ResourceEditForm
from ..models import Resource
from ..selectors import (
    get_or_create_resource_progress,
    get_resource_for_detail,
    get_resource_user_rating,
)

# from ..services import _track_student_first_view

logger = logging.getLogger(__name__)
_recommender = RecommendationService()


class ResourceCreateView(VerifiedTeacherRequiredMixin, CreateView):
    model = Resource
    form_class = ResourceCreateForm
    template_name = "apps/content/resources/form.html"
    success_url = reverse_lazy("content:resource:teacher-resource-list")
    owner_field = "created_by"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["teacher"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, _("Resource created successfully."))
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, _("Please fix the errors below."))
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = _("Create Resource")
        context["submit_label"] = _("Create Resource")
        return context


class ResourceUpdateView(VerifiedTeacherRequiredMixin, OwnerRequiredMixin, UpdateView):
    model = Resource
    form_class = ResourceEditForm
    template_name = "apps/content/resources/form.html"  # reuse create template
    owner_field = "created_by"

    def get_object(self, queryset=None):
        if not hasattr(self, "_object"):
            self._object = (
                Resource.objects.select_related(
                    "course",
                    "grade_subject__grade",
                    "grade_subject__subject",
                )
                .prefetch_related("tags")
                .get(pk=self.kwargs["pk"])
            )
        return self._object

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["teacher"] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse_lazy(
            "content:resource:teacher-resource-detail", kwargs={"pk": self.object.pk}
        )

    def form_valid(self, form):
        messages.success(self.request, _("Resource updated successfully."))
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, _("Please fix the errors below."))
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = _("Edit Resource")
        context["submit_label"] = _("Save Changes")
        context["is_edit"] = True
        return context


class ResourceDeleteView(VerifiedTeacherRequiredMixin, OwnerRequiredMixin, DeleteView):
    model = Resource
    template_name = "apps/content/resources/confirm_delete.html"
    success_url = reverse_lazy("content:resource:teacher-resource-list")
    owner_field = "created_by"

    def form_valid(self, form):
        title = self.get_object().title
        messages.success(
            self.request,
            _(f"Resource {str(title)} deleted successfully.")
            % {"title": self.get_object().title},
        )
        return super().form_valid(form)


class TeacherResourceListView(TeacherRequiredMixin, ListView):
    model = Resource
    template_name = "apps/content/resources/list.html"
    context_object_name = "resources"
    paginate_by = 20

    def get_queryset(self):
        qs = (
            Resource.objects.filter(created_by=self.request.user)
            .select_related("course", "grade_subject")
            .prefetch_related("tags")
            .order_by("-created_at")
        )
        if q := self.request.GET.get("q"):
            qs = qs.filter(title__icontains=q)
        if status := self.request.GET.get("status"):
            qs = qs.filter(status=status)
        if resource_type := self.request.GET.get("resource_type"):
            qs = qs.filter(resource_type=resource_type)
        if difficulty := self.request.GET.get("difficulty"):
            qs = qs.filter(difficulty=difficulty)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        base_qs = Resource.objects.filter(created_by=self.request.user)
        context["total_count"] = base_qs.count()
        context["published_count"] = base_qs.filter(status="published").count()
        context["draft_count"] = base_qs.filter(status="draft").count()
        context["difficulty_choices"] = DifficultyLevel.choices
        context["resource_type_choices"] = ResourceType.choices
        context["filter_q"] = self.request.GET.get("q", "")
        context["filter_status"] = self.request.GET.get("status", "")
        context["filter_resource_type"] = self.request.GET.get("resource_type", "")
        context["filter_difficulty"] = self.request.GET.get("difficulty", "")
        # Preserve filters in pagination links
        params = self.request.GET.copy()
        params.pop("page", None)
        context["querystring"] = params.urlencode()
        return context


# class ResourceDetailView(DetailView):
#     """
#     Generic resource detail view.
#     Works for any ResourceType — template switches on resource.resource_type.
#     Currently wired for EXERCISE; extend template for other types.
#     """

#     model = Resource
#     context_object_name = "resource"
#     pk_url_kwarg = "pk"

#     def get_template_names(self):
#         """
#         Route to type-specific template.
#         Fallback: content/resources/detail.html
#         """
#         type_template_map = {
#             ResourceType.EXERCISE: "apps/content/resources/exercise_detail.html",
#             ResourceType.LESSON: "apps/content/resources/lesson_detail.html",
#             ResourceType.HOMEWORK: "apps/content/resources/homework_detail.html",
#             ResourceType.TEST: "apps/content/resources/test_detail.html",
#             ResourceType.EXAM: "apps/content/resources/exam_detail.html",
#             ResourceType.PAST_PAPER: "apps/content/resources/exam_detail.html",
#             ResourceType.MOCK_EXAM: "apps/content/resources/exam_detail.html",
#             ResourceType.FOREIGN_BOOK: "apps/content/resources/book_detail.html",
#             ResourceType.TEXTBOOK: "apps/content/resources/book_detail.html",
#             ResourceType.STUDY_GUIDE: "apps/content/resources/book_detail.html",
#         }
#         resource_type = getattr(self, "_resource_type", None)
#         return [
#             type_template_map.get(resource_type, "apps/content/resources/detail.html")
#         ]

#     def get(self, request, *args, **kwargs):
#         response = super().get(request, *args, **kwargs)
#         resource = self.object
#         user = request.user

#         # ── Increment view count for everyone, deduped per session ──
#         session_key = f"viewed_resource_{resource.pk}"
#         if not request.session.get(session_key, False):
#             resource.increment_view_count()
#             request.session[session_key] = True

#         resource.refresh_from_db(fields=["view_count", "download_count"])

#         # ── Track progress for authenticated students ──
#         if user.is_authenticated and getattr(user, "is_student", False):
#             self._progress, _ = get_or_create_resource_progress(user, resource)

#         return response

#     def get_object(self, queryset=None):
#         try:
#             resource = get_resource_for_detail(self.kwargs["pk"])
#         except Resource.DoesNotExist:
#             raise Http404("Resource not found or not published.")

#         # Pre-fetch the full hierarchy so the recommender's live-extraction
#         # fallback doesn't fire extra queries if the vector is missing.
#         # If get_resource_for_detail already does select_related, this is a no-op.
#         Resource.objects.filter(pk=resource.pk).select_related(
#             "course__chapter__grade_subject__grade__level",
#             "course__chapter__grade_subject__subject",
#             "course__chapter__grade_subject__specialty",
#             "course__grade_subject__grade__level",
#             "course__grade_subject__subject",
#             "course__grade_subject__specialty",
#             "grade_subject__grade__level",
#             "grade_subject__subject",
#             "grade_subject__specialty",
#         )

#         self._resource_type = resource.resource_type

#         logger.info(
#             "ResourceDetailView accessed",
#             extra={
#                 "user_id": (
#                     self.request.user.id if self.request.user.is_authenticated else None
#                 ),
#                 "resource_pk": str(resource.pk),
#                 "type": resource.resource_type,
#             },
#         )

#         return resource

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         resource = self.object
#         user = self.request.user

#         # ── Breadcrumb context ────────────────────────────────────────────
#         gs = resource.course.effective_grade_subject if resource.course else None
#         grade_subject = gs.subject if gs else resource.grade_subject
#         grade = gs.grade if gs else None
#         level = (
#             grade.level
#             if grade
#             else (grade_subject.subject.level if grade_subject.subject else None)
#         )

#         context.update(
#             {
#                 "grade_subject": grade_subject,
#                 "grade": grade,
#                 "level": level,
#                 "course": resource.course,
#             }
#         )

#         # ── Student-specific context ──────────────────────────────────────
#         is_student = user.is_authenticated and getattr(user, "is_student", False)
#         context["is_student"] = is_student

#         if is_student:
#             progress, _ = get_or_create_resource_progress(user, resource)
#             context["progress"] = progress
#             context["user_rating"] = get_resource_user_rating(user, resource)
#         else:
#             context["progress"] = None
#             context["user_rating"] = None

#         # ── Recommendations ───────────────────────────────────────────────────
#         try:
#             context["recommended_resources"] = _recommender.similar_to(
#                 resource, limit=6
#             )
#         except Exception:
#             # Never let a recommendation failure break the detail page.
#             logger.exception(
#                 "RecommendationService failed for Resource pk=%s", resource.pk
#             )
#             context["recommended_resources"] = []

#         return context


class ResourceDetailView(RatelimitMixin, DetailView):
    """
    Generic resource detail view.
    Works for any ResourceType — template switches on resource.resource_type.
    """

    model = Resource
    context_object_name = "resource"
    pk_url_kwarg = "pk"
    ratelimit_key = "user_or_ip"
    ratelimit_rate = "3/m"  # ← tighten temporarily for testing (normally 120/m)
    ratelimit_method = "GET"
    ratelimit_block = True

    def get_template_names(self):
        type_template_map = {
            ResourceType.EXERCISE: "apps/content/resources/exercise_detail.html",
            ResourceType.LESSON: "apps/content/resources/lesson_detail.html",
            ResourceType.HOMEWORK: "apps/content/resources/homework_detail.html",
            ResourceType.TEST: "apps/content/resources/test_detail.html",
            ResourceType.EXAM: "apps/content/resources/exam_detail.html",
            ResourceType.PAST_PAPER: "apps/content/resources/exam_detail.html",
            ResourceType.MOCK_EXAM: "apps/content/resources/exam_detail.html",
            ResourceType.FOREIGN_BOOK: "apps/content/resources/book_detail.html",
            ResourceType.TEXTBOOK: "apps/content/resources/book_detail.html",
            ResourceType.STUDY_GUIDE: "apps/content/resources/book_detail.html",
        }
        resource_type = getattr(self, "_resource_type", None)
        template = type_template_map.get(
            resource_type, "apps/content/resources/detail.html"
        )

        logger.debug(
            "resource.template_resolved",
            extra={
                "resource_type": resource_type,
                "template": template,
            },
        )

        return [template]

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        resource = self.object
        user = request.user

        # ── View count ────────────────────────────────────────────────────────
        session_key = f"viewed_resource_{resource.pk}"
        if not request.session.get(session_key, False):
            resource.increment_view_count()
            request.session[session_key] = True
            logger.debug(
                "resource.view_count_incremented",
                extra={
                    "resource_id": str(resource.pk),
                    "resource_type": resource.resource_type,
                },
            )
        else:
            logger.debug(
                "resource.view_count_skipped",
                extra={
                    "resource_id": str(resource.pk),
                    "reason": "already_viewed_in_session",
                },
            )

        resource.refresh_from_db(fields=["view_count", "download_count"])

        # ── Progress tracking ─────────────────────────────────────────────────
        if user.is_authenticated and getattr(user, "is_student", False):
            self._progress, created = get_or_create_resource_progress(user, resource)
            logger.debug(
                "resource.progress_fetched",
                extra={
                    "resource_id": str(resource.pk),
                    "user_id": str(user.pk),
                    "created": created,
                },
            )

        return response

    def get_object(self, queryset=None):
        pk = self.kwargs["pk"]
        user = self.request.user

        logger.debug(
            "resource.detail_lookup_started",
            extra={
                "resource_id": str(pk),
                "user_id": str(user.pk) if user.is_authenticated else None,
            },
        )

        try:
            resource = get_resource_for_detail(pk)
        except Resource.DoesNotExist:
            logger.warning(
                "resource.not_found",
                extra={
                    "resource_id": str(pk),
                    "user_id": str(user.pk) if user.is_authenticated else None,
                    "reason": "does_not_exist_or_unpublished",
                },
            )
            raise Http404("Resource not found or not published.")

        self._resource_type = resource.resource_type

        logger.info(
            "resource.detail_viewed",
            extra={
                "resource_id": str(resource.pk),
                "resource_type": resource.resource_type,
                "resource_slug": resource.slug,
                "user_id": str(user.pk) if user.is_authenticated else None,
                "is_free": resource.is_free,
                "status": resource.status,
            },
        )

        return resource

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        resource = self.object
        user = self.request.user

        # ── Breadcrumb context ────────────────────────────────────────────────
        gs = (
            resource.course.effective_grade_subject
            if resource.course
            else resource.grade_subject
        )
        grade = gs.grade if gs else None
        level = grade.level if grade else None
        specialty = gs.specialty if gs else None

        context.update(
            {
                "grade_subject": gs,
                "grade": grade,
                "level": level,
                "course": resource.course,
            }
        )

        # ── Build crumbs ──────────────────────────────────────────────────────
        grade_url = (
            reverse("curriculum:grade:grade-detail", kwargs={"pk": grade.pk})
            if grade
            else "#"
        )
        if specialty and grade:
            grade_url += f"?specialty={specialty.pk}"

        breadcrumbs = [
            {"label": "Home", "url": reverse("pages:landing"), "icon": "fas fa-home"},
            {"label": "Levels", "url": reverse("curriculum:level:level-list")},
        ]

        if level:
            breadcrumbs.append(
                {
                    "label": level.name,
                    "url": reverse(
                        "curriculum:level:level-detail", kwargs={"pk": level.pk}
                    ),
                }
            )

        if grade:
            breadcrumbs.append(
                {
                    "label": f"{grade.name}{' | ' + specialty.short_name if specialty else ''}",
                    "url": grade_url,
                }
            )

        if gs:
            breadcrumbs.append(
                {
                    "label": gs.subject.short_name,
                    "url": reverse(
                        "curriculum:grade-subject:grade-subject-detail",
                        kwargs={"pk": gs.pk},
                    ),
                }
            )

        # Course-based resource → show course in path
        if resource.course:
            breadcrumbs.append(
                {
                    "label": resource.course.title,
                    "url": reverse(
                        "content:course:course-detail",
                        kwargs={"pk": resource.course.pk},
                    ),
                }
            )

        breadcrumbs.append({"label": resource.title, "url": None})

        context["crumbs"] = breadcrumbs
        # ─────────────────────────────────────────────────────────────────────

        # ── Student-specific context ──────────────────────────────────────────
        is_student = user.is_authenticated and getattr(user, "is_student", False)
        context["is_student"] = is_student

        if is_student:
            progress, _ = get_or_create_resource_progress(user, resource)
            context["progress"] = progress
            context["user_rating"] = get_resource_user_rating(user, resource)
        else:
            context["progress"] = None
            context["user_rating"] = None

        # ── Recommendations ───────────────────────────────────────────────────
        try:
            recommendations = _recommender.similar_resources_in_grade_subject(
                grade_subject=gs, limit=6
            )
            context["recommended_resources"] = recommendations
        except Exception:
            logger.exception(
                "resource.recommendations_failed",
                extra={
                    "resource_id": str(resource.pk),
                    "user_id": str(user.pk) if user.is_authenticated else None,
                },
            )
            context["recommended_resources"] = []

        return context


class TeacherResourceDetailView(TeacherRequiredMixin, DetailView):
    model = Resource
    template_name = "apps/content/resources/detail.html"
    context_object_name = "resource"

    def test_func(self):
        resource = self.get_object()
        return (
            self.request.user.role == "teacher"
            and resource.created_by == self.request.user
        )

    def get_object(self, queryset=None):
        # Cache to avoid double DB hit (test_func + get_context_data)
        if not hasattr(self, "_object"):
            self._object = (
                Resource.objects.select_related(
                    "course",
                    "grade_subject__grade",
                    "grade_subject__subject",
                    "created_by",
                )
                .prefetch_related("tags")
                .get(pk=self.kwargs["pk"])
            )
        return self._object

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        # Increment view count on every visit
        self.get_object().increment_view_count()
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        resource = self.get_object()
        context["parent"] = resource.course or resource.grade_subject
        context["parent_type"] = "course" if resource.course else "grade_subject"
        return context


def resource_download_view(request, pk):
    resource = get_object_or_404(Resource, pk=pk, is_active=True)

    if not resource.file:
        raise Http404("File not found.")

    user = request.user

    # ── Increment download count for everyone, deduped per session ──
    session_key = f"downloaded_resource_{resource.pk}"
    if not request.session.get(session_key, False):
        resource.increment_download_count()
        request.session[session_key] = True

    # ── Track progress for authenticated students only ──
    if user.is_authenticated and getattr(user, "is_student", False):
        content_type = ContentType.objects.get_for_model(
            Resource, for_concrete_model=False
        )
        ContentProgress.objects.get_or_create(
            student=user,
            content_type=content_type,
            object_id=resource.pk,
        )

    return FileResponse(
        resource.file.open("rb"),
        content_type=resource.file_mimetype or "application/octet-stream",
        headers={
            "Content-Disposition": f'inline; filename="{resource.original_filename}"'
        },
    )
