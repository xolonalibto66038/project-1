import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import DetailView, ListView

from apps.progress.models import ContentProgress

from ..choices import DifficultyLevel, ResourceType
from ..mixins.course import CourseMixin
from ..models import Course
from ..selectors import (
    get_course_by_pk,
    get_course_exercises,
    get_course_progress,
    get_course_resources,
    resolve_course_breadcrumb,
)
from ..services import record_course_visit

User = get_user_model()

logger = logging.getLogger(__name__)

RESOURCE_TYPE_CONFIG = {
    "lessons": {
        "resource_type": ResourceType.LESSON,
        "tab": "lessons",
        "title": _("Lessons"),
        "icon": "fas fa-chalkboard-teacher",
    },
    "summaries": {
        "resource_type": ResourceType.SUMMARY,
        "tab": "summaries",
        "title": _("Summaries"),
        "icon": "fas fa-align-left",
    },
    "homeworks": {
        "resource_type": ResourceType.HOMEWORK,
        "tab": "homeworks",
        "title": _("Homeworks"),
        "icon": "fas fa-pencil-ruler",
    },
    "exercises": {
        "resource_type": ResourceType.EXERCISE,
        "tab": "exercises",
        "title": _("Exercises"),
        "icon": "fas fa-pencil-alt",
    },
    "notes": {
        "resource_type": ResourceType.NOTES,
        "tab": "notes",
        "title": _("Notes"),
        "icon": "fas fa-sticky-note",
    },
    "series": {
        "resource_type": ResourceType.SERIES,
        "tab": "series",
        "title": _("Series"),
        "icon": "fas fa-layer-group",
    },
}


class CourseDetailView(CourseMixin, DetailView):
    model = Course
    template_name = "apps/content/courses/detail.html"
    context_object_name = "course"
    pk_url_kwarg = "pk"

    def get_object(self, queryset=None):
        # Use our annotated selector instead of the default queryset
        return get_course_by_pk(self.kwargs["pk"])

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        # Record visit for students
        if request.user.is_authenticated and getattr(request.user, "is_student", False):
            with transaction.atomic():
                record_course_visit(request.user, self.object)

        return self.render_to_response(self.get_context_data())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.object
        user = self.request.user
        crumbs = resolve_course_breadcrumb(course)

        context["active_tab"] = "details"
        context["term_display"] = course.get_term_display()
        context["breadcrumb"] = crumbs
        context["level"] = crumbs["level"]
        context["grade"] = crumbs["grade"]
        context["subject"] = crumbs["subject"]
        context["chapter"] = crumbs["chapter"]

        is_matching_student = False
        if self.request.user.is_authenticated and self.request.user.is_student:
            student_grade = getattr(self.request.user.student_profile, "grade", None)
            course_grade = (
                course.effective_grade_subject.grade
                if course.effective_grade_subject
                else None
            )
            is_matching_student = (
                student_grade is not None and student_grade == course_grade
            )

        context["is_matching_student"] = is_matching_student
        context["progress"] = None
        if is_matching_student:
            context["progress"] = get_course_progress(user, course)

        # ── Breadcrumb ────────────────────────────────────────────────────────────
        level = crumbs["level"]
        grade = crumbs["grade"]
        subject = crumbs["subject"]
        chapter = crumbs["chapter"]
        gs = course.effective_grade_subject
        specialty = gs.specialty if gs else None

        grade_url = reverse("curriculum:grade:grade-detail", kwargs={"pk": grade.pk})
        if specialty:
            grade_url += f"?specialty={specialty.pk}"

        breadcrumbs = [
            {"label": "Home", "url": reverse("pages:landing"), "icon": "fas fa-home"},
            {"label": "Levels", "url": reverse("curriculum:level:level-list")},
            {
                "label": level.name,
                "url": reverse(
                    "curriculum:level:level-detail", kwargs={"pk": level.pk}
                ),
            },
            {
                "label": f"{grade.name}{' | ' + specialty.short_name if specialty else ''}",
                "url": grade_url,
            },
            {
                "label": subject.short_name,
                "url": reverse(
                    "curriculum:grade-subject:grade-subject-detail",
                    kwargs={"pk": gs.pk},
                ),
            },
        ]

        if chapter:
            breadcrumbs.append(
                {
                    "label": chapter.title,
                    "url": None,  # add chapter detail URL here if you have one
                }
            )

        breadcrumbs.append({"label": course.title, "url": None})

        context["crumbs"] = breadcrumbs
        # ─────────────────────────────────────────────────────────────────────────

        return context


class CourseExercisesView(CourseMixin, ListView):
    template_name = "apps/content/courses/course_exercises.html"
    context_object_name = "exercises"
    paginate_by = 6

    def get_queryset(self):
        return get_course_exercises(
            course=self.course,
            filters=self.request.GET,
            user=self.request.user,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # preserve GET params for pagination links
        qp = self.request.GET.copy()
        qp.pop("page", None)

        context.update(
            {
                "active_tab": "exercises",
                "difficulty_choices": DifficultyLevel.choices,
                "has_solution_choices": [
                    ("", "— All —"),
                    ("1", "With Solution"),
                    ("0", "Without Solution"),
                ],
                "querystring": qp.urlencode(),
                # active filter values — re-populate form fields
                "filter_q": self.request.GET.get("q", ""),
                "filter_difficulty": self.request.GET.get("difficulty", ""),
                "filter_has_solution": self.request.GET.get("has_solution", ""),
                "filter_completed": self.request.GET.get("completed", ""),
            }
        )

        return context


class CourseVideosView(LoginRequiredMixin, CourseMixin, DetailView):
    model = Course
    template_name = "apps/content/courses/course_videos.html"
    context_object_name = "course"

    def get_queryset(self):
        return Course.objects.select_related(
            "chapter__grade_subject__grade__level",
            "chapter__grade_subject__subject",
            "grade_subject__grade__level",
            "grade_subject__subject",
        ).filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qp = self.request.GET.copy()
        qp.pop("video", None)  # ← strip video so it doesn't duplicate

        course = self.object

        # ── Filters ──────────────────────────────────────────────────
        q = self.request.GET.get("q", "").strip()
        teacher_id = self.request.GET.get("teacher", "").strip()

        videos = course.videos.filter(is_active=True).order_by("order")

        if q:
            videos = videos.filter(
                Q(title__icontains=q) | Q(tags__name__icontains=q)
            ).distinct()

        if teacher_id:
            videos = videos.filter(created_by_id=teacher_id)

        video_pk = self.request.GET.get("video")
        current_video = (
            videos.filter(pk=video_pk).first() if video_pk else None
        ) or videos.first()

        # ── Teachers dropdown — scoped to this course ─────────────────
        teachers = (
            User.objects.filter(
                videos__course=course,
                videos__is_active=True,
            )
            .distinct()
            .only("id", "first_name", "last_name")
        )

        is_student = self.request.user.is_authenticated and getattr(
            self.request.user, "is_student", False
        )

        gs = course.effective_grade_subject
        grade = gs.grade if gs else None
        subject = gs.subject if gs else None
        level = grade.level if grade else None
        specialty = gs.specialty if gs else None
        chapter = course.chapter

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

        if gs and subject:
            breadcrumbs.append(
                {
                    "label": subject.short_name,
                    "url": reverse(
                        "curriculum:grade-subject:grade-subject-detail",
                        kwargs={"pk": gs.pk},
                    ),
                }
            )

        if chapter:
            breadcrumbs.append({"label": chapter.title, "url": None})

        breadcrumbs += [
            {
                "label": course.title,
                "url": reverse(
                    "content:course:course-detail", kwargs={"pk": course.pk}
                ),
            },
            {"label": "Videos", "url": None},
        ]

        context.update(
            {
                "videos": videos,
                "current_video": current_video,
                "is_student": is_student,
                "videos_count": videos.count(),
                "teachers": teachers,
                "filter_q": q,
                "filter_teacher": teacher_id,
                "querystring": qp.urlencode(),
                "grade": grade,
                "subject": subject,
                "level": level,
                "crumbs": breadcrumbs,
            }
        )

        return context


class MarkCourseCompletedView(LoginRequiredMixin, View):

    def post(self, request, pk):

        if not request.user.is_student:
            return redirect("content:course:course-detail", pk=pk)

        course = get_object_or_404(Course, pk=pk)
        content_type = ContentType.objects.get_for_model(Course)

        progress, _ = ContentProgress.objects.get_or_create(
            student=request.user,
            content_type=content_type,
            object_id=course.pk,
        )

        if progress.is_completed:
            progress.mark_incomplete()
        else:
            progress.mark_completed()

        fallback = reverse("content:course:course-detail", kwargs={"pk": pk})
        return redirect(request.META.get("HTTP_REFERER") or fallback)


class CourseResourceListView(CourseMixin, ListView):
    """
    Generic view for all course resource types.
    Driven by `resource_slug` URL kwarg — matches keys in RESOURCE_TYPE_CONFIG.

    URL example:
        path('courses/<uuid:pk>/resources/<str:resource_slug>/',
             CourseResourceListView.as_view(),
             name='course-resources'),
    """

    template_name = "apps/content/courses/resource_list.html"
    context_object_name = "resources"
    paginate_by = 9

    def _get_config(self):
        slug = self.kwargs.get("resource_slug")
        config = RESOURCE_TYPE_CONFIG.get(slug)
        if not config:
            raise Http404(f"Unknown resource type: {slug}")
        return config

    def get_queryset(self):
        config = self._get_config()
        return get_course_resources(
            course=self.course,
            resource_type=config["resource_type"],
            filters=self.request.GET,
            user=self.request.user,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        config = self._get_config()

        course = self.course
        gs = course.effective_grade_subject
        grade = context["grade"]
        level = context["level"]
        subject = context["subject"]
        specialty = gs.specialty if gs else None
        chapter = course.chapter

        qp = self.request.GET.copy()
        qp.pop("page", None)

        grade_url = reverse("curriculum:grade:grade-detail", kwargs={"pk": grade.pk})
        if specialty:
            grade_url += f"?specialty={specialty.pk}"

        breadcrumbs = [
            {"label": "Home", "url": reverse("pages:landing"), "icon": "fas fa-home"},
            {"label": "Levels", "url": reverse("curriculum:level:level-list")},
            {
                "label": level.name,
                "url": reverse(
                    "curriculum:level:level-detail", kwargs={"pk": level.pk}
                ),
            },
            {
                "label": f"{grade.name}{' | ' + specialty.short_name if specialty else ''}",
                "url": grade_url,
            },
            {
                "label": subject.short_name,
                "url": reverse(
                    "curriculum:grade-subject:grade-subject-detail",
                    kwargs={"pk": gs.pk},
                ),
            },
        ]

        if chapter:
            breadcrumbs.append(
                {
                    "label": chapter.title,
                    "url": None,
                }
            )

        breadcrumbs += [
            {
                "label": course.title,
                "url": reverse(
                    "content:course:course-detail", kwargs={"pk": course.pk}
                ),
            },
            {"label": config["title"], "url": None},
        ]

        context.update(
            {
                "active_tab": config["tab"],
                "resource_type_title": config["title"],
                "resource_type_icon": config["icon"],
                "resource_type": config["resource_type"],
                "difficulty_choices": DifficultyLevel.choices,
                "has_solution_choices": [
                    ("", _("— All —")),
                    ("1", _("With Solution")),
                    ("0", _("Without Solution")),
                ],
                "querystring": qp.urlencode(),
                "filter_q": self.request.GET.get("q", ""),
                "filter_difficulty": self.request.GET.get("difficulty", ""),
                "filter_has_solution": self.request.GET.get("has_solution", ""),
                "filter_completed": self.request.GET.get("completed", ""),
                "crumbs": breadcrumbs,
            }
        )

        return context
