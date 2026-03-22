from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, ListView

from apps.content.choices import DifficultyLevel, ResourceType, Term

from ..mixins import GradeSubjectQuarterMixin
from ..models import GradeSubject
from ..services.grade_subject import (
    CoursePageBuilder,
    CourseQueryFilterExtractor,
    CoursesByQuarterCrumbBuilder,
    GradeSubjectCountsProvider,
    GradeSubjectCrumbBuilder,
    GradeSubjectObjectProvider,
    ProgressProviderFactory,
    QuizFilterExtractor,
    QuizQuerysetBuilder,
    QuizSidebarProvider,
    QuizzesCrumbBuilder,
    ResourceFilter,
    ResourceFilterExtractor,
    ResourceListCrumbBuilder,
    ResourceQuerysetBuilder,
    ResourceSidebarProvider,
    ResourceTabConfig,
    ResourceTermGrouper,
    ResourceTypeTitleResolver,
    TermLabelResolver,
)

User = get_user_model()


class GradeSubjectDetailView(DetailView):
    """
    Displays the detail page for a single GradeSubject.

    All data-fetching, configuration, and breadcrumb logic is delegated
    to focused service classes injected via __init__.

    Responsibilities delegated:
        - GradeSubjectObjectProvider   → cached object fetch
        - GradeSubjectCountsProvider   → total + per-quarter content counts
        - ProgressProviderFactory      → selects Student or Anonymous provider
        - ResourceTabConfig            → tab definitions (not view logic)
        - GradeSubjectCrumbBuilder     → breadcrumb trail with specialty URL
    """

    model = GradeSubject
    template_name = "apps/curriculum/grade_subjects/detail.html"
    context_object_name = "grade_subject"

    # ── Dependency injection ──────────────────────────────────────────────────

    def __init__(
        self,
        object_provider: GradeSubjectObjectProvider | None = None,
        counts_provider: GradeSubjectCountsProvider | None = None,
        progress_factory: ProgressProviderFactory | None = None,
        tab_config: ResourceTabConfig | None = None,
        breadcrumb_builder: GradeSubjectCrumbBuilder | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.object_provider = object_provider or GradeSubjectObjectProvider()
        self.counts_provider = counts_provider or GradeSubjectCountsProvider()
        self.progress_factory = progress_factory or ProgressProviderFactory()
        self.tab_config = tab_config or ResourceTabConfig()
        self.breadcrumb_builder = breadcrumb_builder or GradeSubjectCrumbBuilder()

    # ── Object ────────────────────────────────────────────────────────────────

    def get_object(self, queryset=None) -> object:
        return self.object_provider.get(pk=self.kwargs["pk"])

    # ── Context ───────────────────────────────────────────────────────────────

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)

        gs = self.object
        user = self.request.user
        pk = gs.pk

        counts = self.counts_provider.get_counts(pk)
        counts_by_quarter = self.counts_provider.get_by_quarter(pk)

        progress_provider = self.progress_factory.for_user(user)
        progress = progress_provider.get_progress(user, pk)

        self._dispatch_messages(gs, counts, progress)

        context.update(
            {
                "grade": gs.grade,
                "level": gs.grade.level,
                "subject": gs.subject,
                "specialty": gs.specialty,
                "is_student": self.progress_factory.for_user(user).__class__.__name__
                == "StudentProgressProvider",
                "quarters": Term.choices,
                "current_quarter": Term.FIRST,
                "course_count": counts["course_count"],
                "resource_count": counts["resource_count"],
                "quiz_count": counts["quiz_count"],
                "counts_by_quarter": counts_by_quarter,
                "completed_courses": progress["completed_courses"],
                "progress_pct": progress["progress_pct"],
                "subject_resource_tabs": self.tab_config.get_tabs(),
                "crumbs": self.breadcrumb_builder.build_for_grade_subject(gs),
                "page_title": gs.subject.short_name,
                "page_description": _(
                    "Courses, resources, and quizzes for this subject."
                ),
            }
        )

        return context

    # ── Private ───────────────────────────────────────────────────────────────

    def _dispatch_messages(
        self,
        gs: object,
        counts: dict,
        progress: dict,
    ) -> None:
        if counts.get("course_count", 0) == 0:
            messages.info(
                self.request,
                _("No courses have been added to this subject yet."),
            )

        if progress.get("progress_pct", 0) == 100:
            messages.success(
                self.request,
                _("You have completed all courses in this subject. Well done!"),
            )


class GradeSubjectCoursesByQuarterView(GradeSubjectQuarterMixin, ListView):
    """
    Lists courses for a GradeSubject filtered by quarter, difficulty,
    and search query.

    Responsibilities delegated:
        - GradeSubjectQuarterMixin      → grade_subject + get_term()
        - CourseQueryFilterExtractor    → GET param extraction + cleaning
        - CoursePageBuilder             → course list construction
        - TermLabelResolver             → term key → display string
        - CoursesByQuarterCrumbBuilder  → 5-crumb breadcrumb trail
    """

    template_name = "apps/curriculum/grade_subjects/courses_by_quarter.html"
    context_object_name = "courses"
    paginate_by = 10

    # ── Dependency injection ──────────────────────────────────────────────────

    def __init__(
        self,
        filter_extractor: CourseQueryFilterExtractor | None = None,
        course_builder: CoursePageBuilder | None = None,
        term_resolver: TermLabelResolver | None = None,
        breadcrumb_builder: CoursesByQuarterCrumbBuilder | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.filter_extractor = filter_extractor or CourseQueryFilterExtractor()
        self.course_builder = course_builder or CoursePageBuilder()
        self.term_resolver = term_resolver or TermLabelResolver(Term.choices)
        self.breadcrumb_builder = breadcrumb_builder or CoursesByQuarterCrumbBuilder()

    # ── Queryset ──────────────────────────────────────────────────────────────

    def get_queryset(self) -> list:
        self._filters = self.filter_extractor.extract(self.request)
        return self.course_builder.build(
            grade_subject=self.grade_subject,
            quarter=self.kwargs.get("quarter"),
            user=self.request.user,
            filters=self._filters,
        )

    # ── Context ───────────────────────────────────────────────────────────────

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)

        gs = self.grade_subject
        term = self.get_term()
        filters = self._filters  # already extracted in get_queryset
        quarter_display = self.term_resolver.resolve(term)

        self._dispatch_messages(context)

        context.update(
            {
                "difficulty_choices": DifficultyLevel.choices,
                "current_difficulty": filters.difficulty or "",
                "current_search": filters.search or "",
                "querystring": filters.querystring,
                "quarter_display": quarter_display,
                "is_student": (
                    self.request.user.is_authenticated
                    and getattr(self.request.user, "is_student", False)
                ),
                "crumbs": self.breadcrumb_builder.build_for_courses_by_quarter(
                    gs, quarter_display
                ),
                "page_title": _("%(subject)s — %(quarter)s")
                % {
                    "subject": gs.subject.short_name,
                    "quarter": quarter_display,
                },
            }
        )

        return context

    # ── Private ───────────────────────────────────────────────────────────────

    def _dispatch_messages(self, context: dict) -> None:
        page_obj = context.get("page_obj")
        if page_obj is not None and not page_obj.object_list:
            messages.info(
                self.request,
                _("No courses found for this quarter and filter combination."),
            )


class GradeSubjectResourceListByTermView(ListView):
    """
    Lists published resources for a GradeSubject, filtered by term,
    resource type, and 6 additional filter params.

    Operates in two modes:
      - Filtered mode  (active_term set)  → paginated flat list
      - Grouping mode  (no active_term)   → unpaginated, grouped by term

    Responsibilities delegated:
        - ResourceFilterExtractor      → 8 GET params + URL kwarg priority
        - ResourceQuerysetBuilder      → ORM + 8 filter conditions
        - ResourceTypeTitleResolver    → slug → display label
        - ResourceSidebarProvider      → courses + teachers sidebar
        - ResourceTermGrouper          → group-by-term for grouping mode
        - ResourceListCrumbBuilder     → 6-crumb breadcrumb trail
    """

    model = GradeSubject  # overridden by get_queryset
    template_name = "apps/curriculum/grade_subjects/resources_by_term.html"
    context_object_name = "resources"

    # ── Dependency injection ──────────────────────────────────────────────────

    def __init__(
        self,
        filter_extractor: ResourceFilterExtractor | None = None,
        queryset_builder: ResourceQuerysetBuilder | None = None,
        title_resolver: ResourceTypeTitleResolver | None = None,
        sidebar_provider: ResourceSidebarProvider | None = None,
        term_grouper: ResourceTermGrouper | None = None,
        breadcrumb_builder: ResourceListCrumbBuilder | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.filter_extractor = filter_extractor or ResourceFilterExtractor()
        self.queryset_builder = queryset_builder or ResourceQuerysetBuilder()
        self.title_resolver = title_resolver or ResourceTypeTitleResolver()
        self.sidebar_provider = sidebar_provider or ResourceSidebarProvider()
        self.term_grouper = term_grouper or ResourceTermGrouper()
        self.breadcrumb_builder = breadcrumb_builder or ResourceListCrumbBuilder()

    # ── Setup ─────────────────────────────────────────────────────────────────

    def setup(self, request, *args, **kwargs) -> None:
        super().setup(request, *args, **kwargs)
        self.grade_subject = get_object_or_404(
            GradeSubject.objects.select_related("grade", "subject", "specialty"),
            pk=self.kwargs["pk"],
            is_active=True,
        )
        self.current_term = self.kwargs.get("term")
        self.resource_slug = self.kwargs.get("resource_slug")

    # ── Pagination — dynamic based on active term ─────────────────────────────

    @property
    def paginate_by(self) -> int | None:
        if self.current_term or self.request.GET.get("term"):
            return 15
        return None

    # ── Queryset ──────────────────────────────────────────────────────────────

    def get_queryset(self):
        self._filters = self.filter_extractor.extract(
            self.request,
            current_term=self.current_term,
            resource_slug=self.resource_slug,
        )
        return self.queryset_builder.build(self.grade_subject, self._filters)

    # ── Context ───────────────────────────────────────────────────────────────

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)

        gs = self.grade_subject
        filters = self._filters
        sidebar = self.sidebar_provider.fetch(gs)
        resource_type_title = self.title_resolver.resolve(self.resource_slug)

        self._dispatch_messages(context, filters)

        context.update(
            {
                "grade_subject": gs,
                "resource_slug": self.resource_slug,
                "level": gs.grade.level,
                "grade": gs.grade,
                "subject": gs.subject,
                "specialty": gs.specialty,
                "current_term": self.current_term,
                "resource_type_title": resource_type_title,
                "resource_type_icon": "fas fa-file-alt",
                "difficulty_choices": DifficultyLevel.choices,
                "term_choices": Term.choices,
                "resource_type_choices": ResourceType.get_subject_choices(),
                "courses": sidebar.courses,
                "teachers": sidebar.teachers,
                "filter_q": filters.q or "",
                "filter_difficulty": filters.difficulty or "",
                "filter_term": filters.term or "",
                "filter_resource_type": filters.resource_type or "",
                "filter_has_solution": filters.has_solution or "",
                "filter_is_free": filters.is_free or "",
                "filter_course": filters.course or "",
                "filter_teacher": filters.teacher or "",
                "querystring": filters.querystring,
                "crumbs": self.breadcrumb_builder.build_for_resources(
                    gs, resource_type_title
                ),
                "page_title": resource_type_title,
            }
        )

        # Grouping mode — only when no term is active
        if not filters.active_term:
            context["resources_by_term"] = self.term_grouper.group(
                context["object_list"],
                Term.choices,
            )

        return context

    # ── Private ───────────────────────────────────────────────────────────────

    def _dispatch_messages(self, context: dict, filters: ResourceFilter) -> None:
        page_obj = context.get("page_obj")
        if page_obj is not None and not page_obj.object_list:
            messages.info(
                self.request,
                _("No resources match your current filters."),
            )
        elif not context.get("object_list"):
            messages.info(
                self.request,
                _("No resources have been added to this subject yet."),
            )


class GradeSubjectQuizzesView(GradeSubjectQuarterMixin, ListView):
    """
    Lists published quizzes for a GradeSubject with filtering by
    search query, course, teacher, and auto-gradable flag.

    Responsibilities delegated:
        - GradeSubjectQuarterMixin  → grade_subject resolution
        - QuizFilterExtractor       → 4 GET params → QuizFilter dataclass
        - QuizQuerysetBuilder       → filtered + annotated ORM queryset
        - QuizSidebarProvider       → courses + teachers sidebar data
        - QuizzesCrumbBuilder       → 6-crumb breadcrumb trail
    """

    template_name = "apps/curriculum/grade_subjects/quizzes.html"
    context_object_name = "quizzes"
    paginate_by = 12

    # ── Dependency injection ──────────────────────────────────────────────────

    def __init__(
        self,
        filter_extractor: QuizFilterExtractor | None = None,
        queryset_builder: QuizQuerysetBuilder | None = None,
        sidebar_provider: QuizSidebarProvider | None = None,
        breadcrumb_builder: QuizzesCrumbBuilder | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.filter_extractor = filter_extractor or QuizFilterExtractor()
        self.queryset_builder = queryset_builder or QuizQuerysetBuilder()
        self.sidebar_provider = sidebar_provider or QuizSidebarProvider()
        self.breadcrumb_builder = breadcrumb_builder or QuizzesCrumbBuilder()

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def dispatch(self, request, *args, **kwargs):
        self.get_grade_subject()
        return super().dispatch(request, *args, **kwargs)

    # ── Queryset ──────────────────────────────────────────────────────────────

    def get_queryset(self):
        self._filters = self.filter_extractor.extract(self.request)
        return self.queryset_builder.build(self.grade_subject, self._filters)

    # ── Context ───────────────────────────────────────────────────────────────

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)

        gs = self.grade_subject
        filters = self._filters
        sidebar = self.sidebar_provider.fetch(gs)

        self._dispatch_messages(context)

        context.update(
            {
                "filter_q": filters.q or "",
                "filter_course": filters.course_id or "",
                "filter_teacher": filters.teacher_id or "",
                "filter_auto_grade": filters.auto_grade or "",
                "querystring": filters.querystring,
                "courses": sidebar.courses,
                "teachers": sidebar.teachers,
                "crumbs": self.breadcrumb_builder.build_for_quizzes(gs),
                "page_title": _("Quizzes — %(subject)s")
                % {"subject": gs.subject.short_name},
            }
        )

        return context

    # ── Private ───────────────────────────────────────────────────────────────

    def _dispatch_messages(self, context: dict) -> None:
        page_obj = context.get("page_obj")
        if page_obj is not None and not page_obj.object_list:
            messages.info(
                self.request,
                _("No quizzes match your current filters."),
            )
