import logging

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import DetailView, ListView

from apps.authentication.mixins import StudentRequiredMixin

from ..choices import DifficultyLevel, Term
from ..mixins.course import CourseMixin, CourseSubViewMixin
from ..models import Course
from ..selectors import get_course_by_pk, resolve_course_breadcrumb
from ..services.course import (
    HAS_SOLUTION_CHOICES,
    CourseCompletionToggler,
    CourseCrumbBuilder,
    CourseProgressProvider,
    CourseQuizFilterExtractor,
    CourseQuizQuerysetBuilder,
    CourseQuizzesCrumbBuilder,
    CourseResourceCrumbBuilder,
    CourseResourceFilterExtractor,
    CourseResourceQuerysetBuilder,
    CourseVideosCrumbBuilder,
    CourseVisitRecorder,
    CourseVisitRecorderProtocol,
    CurrentVideoSelector,
    ResourceTypeConfigResolver,
    StudentGradeMatchChecker,
    VideoFilterExtractor,
    VideoQuerysetBuilder,
    VideoTeacherProvider,
)

User = get_user_model()
EMPTY_COURSE_QS = Course.objects.none()
logger = logging.getLogger(__name__)


class CourseDetailView(CourseMixin, DetailView):
    """
    Displays the detail page for a single Course.

    The get() override intentionally records a student visit as a
    side effect before rendering — this is the correct lifecycle
    placement (not in get_context_data, which may be called multiple
    times in testing).

    Responsibilities delegated:
        - CourseVisitRecorder          → atomic visit recording
        - StudentGradeMatchChecker     → student × course grade matching
        - CourseProgressProvider       → progress data for matching students
        - CourseCrumbBuilder           → dynamic breadcrumb chain
    """

    model = Course
    template_name = "apps/content/courses/detail.html"
    context_object_name = "course"
    pk_url_kwarg = "pk"

    # ── Dependency injection ──────────────────────────────────────────────────

    def __init__(
        self,
        visit_recorder: CourseVisitRecorderProtocol | None = None,
        grade_match_checker: StudentGradeMatchChecker | None = None,
        progress_provider: CourseProgressProvider | None = None,
        breadcrumb_builder: CourseCrumbBuilder | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.visit_recorder = visit_recorder or CourseVisitRecorder()
        self.grade_match_checker = grade_match_checker or StudentGradeMatchChecker()
        self.progress_provider = progress_provider or CourseProgressProvider()
        self.breadcrumb_builder = breadcrumb_builder or CourseCrumbBuilder()

    # ── Object ────────────────────────────────────────────────────────────────

    def get_object(self, queryset=None) -> object:
        return get_course_by_pk(self.kwargs["pk"])

    # ── Request lifecycle ─────────────────────────────────────────────────────

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        if request.user.is_authenticated and getattr(request.user, "is_student", False):
            self.visit_recorder.record(request.user, self.object)

        return self.render_to_response(self.get_context_data())

    # ── Context ───────────────────────────────────────────────────────────────

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)

        course = self.object
        user = self.request.user

        crumb_data = resolve_course_breadcrumb(course)
        is_matching_student = self.grade_match_checker.is_matching(user, course)
        progress = self.progress_provider.get_progress(
            user, course, is_matching_student
        )

        self._dispatch_messages(course, is_matching_student, progress)

        context.update(
            {
                "active_tab": "details",
                "term_display": course.get_term_display(),
                "level": crumb_data["level"],
                "grade": crumb_data["grade"],
                "subject": crumb_data["subject"],
                "chapter": crumb_data["chapter"],
                "is_matching_student": is_matching_student,
                "progress": progress,
                "crumbs": self.breadcrumb_builder.build_for_course(course, crumb_data),
                "page_title": course.title,
            }
        )

        return context

    # ── Private ───────────────────────────────────────────────────────────────

    def _dispatch_messages(
        self,
        course: object,
        is_matching_student: bool,
        progress: object | None,
    ) -> None:
        if progress and getattr(progress, "progress_pct", 0) == 100:
            messages.success(
                self.request,
                _("You have completed this course. Well done!"),
            )

        if not is_matching_student and self.request.user.is_authenticated:
            messages.info(
                self.request,
                _("You are viewing this course outside your enrolled grade."),
            )


class CourseVideosView(LoginRequiredMixin, CourseMixin, DetailView):
    """
    Displays the video player page for a course.

    is_student is resolved once in setup() and flows through to
    VideoQuerysetBuilder (controls annotation) and context — never
    recomputed.

    Responsibilities delegated:
        - VideoFilterExtractor      → q + teacher + video param
        - VideoQuerysetBuilder      → filter + conditional annotation
        - VideoStudentAnnotator     → 4 subqueries (inside builder)
        - CurrentVideoSelector      → active video from param or first
        - VideoTeacherProvider      → sidebar teachers query
        - CourseVideosCrumbBuilder  → null-safe optional crumb chain
    """

    model = Course
    template_name = "apps/content/courses/course_videos.html"
    context_object_name = "course"

    # ── Dependency injection ──────────────────────────────────────────────────

    def __init__(
        self,
        filter_extractor: VideoFilterExtractor | None = None,
        queryset_builder: VideoQuerysetBuilder | None = None,
        video_selector: CurrentVideoSelector | None = None,
        teacher_provider: VideoTeacherProvider | None = None,
        breadcrumb_builder: CourseVideosCrumbBuilder | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.filter_extractor = filter_extractor or VideoFilterExtractor()
        self.queryset_builder = queryset_builder or VideoQuerysetBuilder()
        self.video_selector = video_selector or CurrentVideoSelector()
        self.teacher_provider = teacher_provider or VideoTeacherProvider()
        self.breadcrumb_builder = breadcrumb_builder or CourseVideosCrumbBuilder()

    # ── Setup — is_student resolved exactly once ──────────────────────────────

    def setup(self, request, *args, **kwargs) -> None:
        super().setup(request, *args, **kwargs)
        self._is_student = request.user.is_authenticated and getattr(
            request.user, "is_student", False
        )
        self._filters = self.filter_extractor.extract(request)

    # ── Queryset (DetailView) ─────────────────────────────────────────────────

    def get_queryset(self):
        return Course.objects.select_related(
            "chapter__grade_subject__grade__level",
            "chapter__grade_subject__subject",
            "grade_subject__grade__level",
            "grade_subject__subject",
        ).filter(is_active=True)

    # ── Context ───────────────────────────────────────────────────────────────

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)

        course = self.object
        user = self.request.user
        filters = self._filters
        is_student = self._is_student

        videos = self.queryset_builder.build(
            course=course,
            filters=filters,
            is_student=is_student,
            user=user,
        )

        current_video = self.video_selector.select(videos, filters.video_pk)
        teachers = self.teacher_provider.fetch(course)

        context.update(
            {
                "videos": videos,
                "current_video": current_video,
                "videos_count": videos.count(),
                "is_student": is_student,
                "current_video_bookmarked": (
                    getattr(current_video, "is_bookmarked", False)
                    if is_student and current_video
                    else False
                ),
                "teachers": teachers,
                "filter_q": filters.q or "",
                "filter_teacher": filters.teacher_id or "",
                "querystring": filters.querystring,
                "grade": context.get("grade"),
                "subject": context.get("subject"),
                "level": context.get("level"),
                "crumbs": self.breadcrumb_builder.build_for_videos(course),
                "page_title": _("%(title)s — Videos") % {"title": course.title},
            }
        )

        return context


class CourseResourceListView(CourseMixin, ListView):
    """
    Generic resource list view driven by ``resource_slug`` URL kwarg.

    The config is resolved once in ``setup()`` and cached as
    ``self._config`` — both ``get_queryset`` and ``get_context_data``
    read it from there, eliminating the double-lookup anti-pattern.

    Responsibilities delegated:
        - ResourceTypeConfigResolver      → slug → config or Http404
        - CourseResourceFilterExtractor   → GET params → dataclass
        - CourseResourceQuerysetBuilder   → queryset via config
        - CourseResourceCrumbBuilder      → dynamic breadcrumb chain
    """

    template_name = "apps/content/courses/resource_list.html"
    context_object_name = "resources"
    paginate_by = 9

    # ── Dependency injection ──────────────────────────────────────────────────

    def __init__(
        self,
        config_resolver: ResourceTypeConfigResolver | None = None,
        filter_extractor: CourseResourceFilterExtractor | None = None,
        queryset_builder: CourseResourceQuerysetBuilder | None = None,
        breadcrumb_builder: CourseResourceCrumbBuilder | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.config_resolver = config_resolver or ResourceTypeConfigResolver()
        self.filter_extractor = filter_extractor or CourseResourceFilterExtractor()
        self.queryset_builder = queryset_builder or CourseResourceQuerysetBuilder()
        self.breadcrumb_builder = breadcrumb_builder or CourseResourceCrumbBuilder()

    # ── Setup — config resolved exactly once ─────────────────────────────────

    def setup(self, request, *args, **kwargs) -> None:
        super().setup(request, *args, **kwargs)
        # Http404 raised here if slug is unknown — before any DB work
        self._config = self.config_resolver.resolve(self.kwargs.get("resource_slug"))
        self._filters = self.filter_extractor.extract(request)

    # ── Queryset ──────────────────────────────────────────────────────────────

    def get_queryset(self):
        return self.queryset_builder.build(
            course=self.course,
            config=self._config,
            request_GET=self.request.GET,
            user=self.request.user,
        )

    # ── Context ───────────────────────────────────────────────────────────────

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)

        config = self._config
        filters = self._filters
        course = self.course

        self._dispatch_messages(context)

        context.update(
            {
                "active_tab": config["tab"],
                "resource_type_title": config["title"],
                "resource_type_icon": config["icon"],
                "resource_type": config["resource_type"],
                "difficulty_choices": DifficultyLevel.choices,
                "has_solution_choices": HAS_SOLUTION_CHOICES,
                "querystring": filters.querystring,
                "filter_q": filters.q or "",
                "filter_difficulty": filters.difficulty or "",
                "filter_has_solution": filters.has_solution or "",
                "filter_completed": filters.completed or "",
                "crumbs": self.breadcrumb_builder.build_for_course_resources(
                    course=course,
                    config=config,
                    level=context["level"],
                    grade=context["grade"],
                    subject=context["subject"],
                ),
                "page_title": config["title"],
            }
        )

        return context

    # ── Private ───────────────────────────────────────────────────────────────

    def _dispatch_messages(self, context: dict) -> None:
        page_obj = context.get("page_obj")
        if page_obj is not None and not page_obj.object_list:
            messages.info(
                self.request,
                _("No resources found for this filter combination."),
            )


class CourseQuizzesView(
    LoginRequiredMixin, CourseSubViewMixin, CourseMixin, DetailView
):
    """
    Displays quizzes for a course, filtered by search, teacher,
    auto-gradable flag, and term.

    Responsibilities delegated:
        - CourseSubViewMixin         → is_student + get_queryset
        - CourseQuizFilterExtractor  → 4 params → dataclass
        - CourseQuizQuerysetBuilder  → ORM + user-scoped annotations
        - VideoTeacherProvider       → sidebar teachers (shared service)
        - CourseQuizzesCrumbBuilder  → null-safe crumb chain (extends videos builder)

    ``courses`` context key is an empty queryset — kept for template
    compatibility with the shared quiz filter partial that expects this key.
    """

    model = Course
    template_name = "apps/content/courses/quizzes.html"
    context_object_name = "course"

    # ── Dependency injection ──────────────────────────────────────────────────

    def __init__(
        self,
        filter_extractor: CourseQuizFilterExtractor | None = None,
        queryset_builder: CourseQuizQuerysetBuilder | None = None,
        teacher_provider: VideoTeacherProvider | None = None,
        breadcrumb_builder: CourseQuizzesCrumbBuilder | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.filter_extractor = filter_extractor or CourseQuizFilterExtractor()
        self.queryset_builder = queryset_builder or CourseQuizQuerysetBuilder()
        self.teacher_provider = teacher_provider or VideoTeacherProvider()
        self.breadcrumb_builder = breadcrumb_builder or CourseQuizzesCrumbBuilder()

    # ── Setup ─────────────────────────────────────────────────────────────────

    def setup(self, request, *args, **kwargs) -> None:
        super().setup(request, *args, **kwargs)  # CourseSubViewMixin sets _is_student
        self._filters = self.filter_extractor.extract(request)

    # ── Context ───────────────────────────────────────────────────────────────

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)

        course = self.object
        user = self.request.user
        filters = self._filters
        is_student = self._is_student

        quizzes = self.queryset_builder.build(course, filters, user)
        teachers = self.teacher_provider.fetch(course)

        self._dispatch_messages(quizzes)

        context.update(
            {
                "quizzes": quizzes,
                "is_student": is_student,
                "grade_subject": course.effective_grade_subject,
                "subject": context.get("subject"),
                "grade": context.get("grade"),
                "level": context.get("level"),
                "teachers": teachers,
                "term_choices": Term.choices,
                "filter_q": filters.q or "",
                "filter_teacher": filters.teacher_id or "",
                "filter_auto_grade": filters.auto_grade or "",
                "filter_term": filters.term or "",
                "filter_course": "",
                "courses": EMPTY_COURSE_QS,
                "querystring": filters.querystring,
                "active_tab": "quizzes",
                "crumbs": self.breadcrumb_builder.build_for_quizzes(course),
                "page_title": _("%(title)s — Quizzes") % {"title": course.title},
            }
        )

        return context

    # ── Private ───────────────────────────────────────────────────────────────

    def _dispatch_messages(self, quizzes) -> None:
        if not quizzes.exists():
            messages.info(
                self.request,
                _("No quizzes are available for this course yet."),
            )


class MarkCourseCompletedView(StudentRequiredMixin, View):
    """
    Toggles course completion state for the authenticated student.

    StudentRequiredMixin enforces the student check before post() is
    called — the redundant inline check is removed.

    Responsibilities delegated:
        - CourseCompletionToggler → get_or_create + toggle + return new state
    """

    # ── Dependency injection ──────────────────────────────────────────────────

    def __init__(
        self,
        toggler: CourseCompletionToggler | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.toggler = toggler or CourseCompletionToggler()

    # ── POST ──────────────────────────────────────────────────────────────────

    def post(self, request, pk):
        course = get_object_or_404(Course, pk=pk)
        is_completed = self.toggler.toggle(request.user, course)

        if is_completed:
            messages.success(
                request,
                _("%(title)s marked as completed.") % {"title": course.title},
            )
        else:
            messages.info(
                request,
                _("%(title)s marked as incomplete.") % {"title": course.title},
            )

        fallback = reverse("content:course:course-detail", kwargs={"pk": pk})
        return redirect(request.META.get("HTTP_REFERER") or fallback)
