import logging
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from django.db.models import Count, Q, QuerySet
from django.http import HttpRequest
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from .level import BreadcrumbBuilder

logger = logging.getLogger(__name__)


def build_grade_subject_courses_page(
    grade_subject, quarter: str, user=None, difficulty=None, search=None
):
    """
    Returns annotated course list for SubjectCoursesByQuarterView.
    Thin wrapper — keeps the view free of selector imports.
    """
    from ..selectors.grade_subject import get_grade_subject_courses_by_quarter

    return get_grade_subject_courses_by_quarter(
        grade_subject=grade_subject,
        quarter=quarter,
        user=user,
        difficulty=difficulty,
        search=search,
    )


@runtime_checkable
class ProgressProviderProtocol(Protocol):
    """
    Inversion boundary for grade-subject progress data.

    Both StudentProgressProvider and AnonymousProgressStub satisfy this
    protocol — the view never needs to branch on user role.
    """

    def get_progress(self, user: object, grade_subject_pk: int) -> dict: ...


@dataclass(frozen=True)
class ProgressResult:
    completed_courses: int
    total_courses: int
    progress_pct: float


class StudentProgressProvider:
    """
    Single responsibility: fetch real progress data for an authenticated student.
    """

    def get_progress(self, user: object, grade_subject_pk: int) -> dict:
        from ..selectors.grade_subject import get_grade_subject_progress_for_student

        return get_grade_subject_progress_for_student(user, grade_subject_pk)


class AnonymousProgressStub:
    """
    Single responsibility: return a zero-filled progress structure for
    non-student users.

    Satisfies ProgressProviderProtocol (LSP) — the view calls the same
    interface regardless of which provider it receives.
    """

    def get_progress(self, user: object, grade_subject_pk: int) -> dict:
        return {
            "completed_courses": 0,
            "total_courses": 0,
            "progress_pct": 0,
        }


class ProgressProviderFactory:
    """
    Single responsibility: select the correct ProgressProvider based on
    the user's role.

    Keeps the branching logic in one place — the view never inspects
    `is_student` directly.
    """

    def __init__(
        self,
        student_provider: ProgressProviderProtocol | None = None,
        anonymous_provider: ProgressProviderProtocol | None = None,
    ) -> None:
        self._student = student_provider or StudentProgressProvider()
        self._anonymous = anonymous_provider or AnonymousProgressStub()

    def for_user(self, user: object) -> ProgressProviderProtocol:
        is_student = user.is_authenticated and getattr(user, "is_student", False)
        return self._student if is_student else self._anonymous


class GradeSubjectCountsProvider:
    """
    Single responsibility: retrieve aggregated content counts for a
    GradeSubject — both totals and the per-quarter breakdown.

    Open for extension — override ``get_counts`` or ``get_by_quarter``
    to add caching or alternate data sources without touching the view.
    """

    def get_counts(self, grade_subject_pk: int) -> dict:
        from ..selectors.grade_subject import get_grade_subject_counts

        return get_grade_subject_counts(pk=grade_subject_pk)

    def get_by_quarter(self, grade_subject_pk: int) -> dict:
        from ..selectors.grade_subject import get_grade_subject_counts_by_quarter

        return get_grade_subject_counts_by_quarter(pk=grade_subject_pk)


@dataclass(frozen=True)
class ResourceTab:
    """Immutable descriptor for a single resource-type tab."""

    slug: str
    label: str
    icon: str


class ResourceTabConfig:
    """
    Single responsibility: own the canonical list of resource tabs for
    the grade-subject detail page.

    Defined here as a class (not inline tuples) so it can be:
    - subclassed to add/remove tabs per deployment (OCP)
    - imported and tested independently of the view
    - iterated in templates as structured objects, not raw tuples
    """

    TABS: list[ResourceTab] = [
        ResourceTab("test", _("Tests"), "fas fa-clipboard-check"),
        ResourceTab("exam", _("Exams"), "fas fa-file-alt"),
        ResourceTab("past_paper", _("Past Papers"), "fas fa-file-signature"),
        ResourceTab("mock_exam", _("Mock Exams"), "fas fa-stopwatch"),
        ResourceTab("textbook", _("Textbooks"), "fas fa-book-open"),
        ResourceTab("foreign_book", _("Foreign Books"), "fas fa-book"),
        ResourceTab("study_guide", _("Study Guides"), "fas fa-book-reader"),
    ]

    def get_tabs(self) -> list[ResourceTab]:
        return self.TABS


class GradeSubjectObjectProvider:
    """
    Single responsibility: fetch and cache the GradeSubject instance
    for the duration of the request.

    The caching pattern (_cache attribute) lives here — not as a
    private method cluttering the view. The view calls ``get``; it never
    manages the cache itself.
    """

    def __init__(self) -> None:
        self._cache: object | None = None

    def get(self, pk: int) -> object:
        if self._cache is None:
            from ..selectors.grade_subject import get_grade_subject_by_pk

            self._cache = get_grade_subject_by_pk(pk=pk)
            if self._cache is None:
                logger.warning(
                    "GradeSubjectObjectProvider: no GradeSubject found for pk=%s.", pk
                )
        return self._cache


class GradeSubjectCrumbBuilder(BreadcrumbBuilder):
    """
    Extends BreadcrumbBuilder (OCP) with the level + grade crumbs,
    then appends the subject as the terminal crumb.

    Grade URL is enriched with ?specialty=<pk> when a specialty is
    present — this IDOR-safe construction lives here, not in the view.
    """

    CRUMB_DEFINITIONS: list[dict] = [
        {"label": _("Home"), "url_name": "pages:landing", "icon": "fas fa-home"},
        {"label": _("Levels"), "url_name": "curriculum:level:level-list"},
    ]

    def build_for_grade_subject(
        self,
        grade_subject: object,
    ) -> list[dict]:
        grade = grade_subject.grade
        level = grade.level
        subject = grade_subject.subject
        specialty = grade_subject.specialty

        crumbs = self.build()

        crumbs.append(
            {
                "label": level.get_name_display(),
                "url": reverse(
                    "curriculum:level:level-detail",
                    kwargs={"pk": level.pk},
                ),
            }
        )

        grade_url = reverse(
            "curriculum:grade:grade-detail",
            kwargs={"pk": grade.pk},
        )
        if specialty:
            grade_url += f"?specialty={specialty.pk}"

        grade_label = grade.short_name
        if specialty:
            grade_label = f"{grade_label} | {specialty.short_name}"

        crumbs.append({"label": grade_label, "url": grade_url})
        crumbs.append({"label": subject.short_name, "url": None})

        return crumbs


@dataclass(frozen=True)
class CourseQueryFilter:
    """
    Immutable value object carrying all active filter parameters
    for the courses-by-quarter page.

    Passed as a unit to CoursePageBuilder — no loose kwargs threading
    through multiple methods.
    """

    difficulty: str | None
    search: str | None
    querystring: str  # pagination-stripped, safe for template hrefs


class CourseQueryFilterExtractor:
    """
    Single responsibility: extract, clean, and package GET parameters
    into a CourseQueryFilter value object.

    Open for extension — subclass and override ``extract`` to add new
    filter params (e.g. ``sort``, ``tag``) without touching the view
    or the builder.
    """

    DIFFICULTY_PARAM = "difficulty"
    SEARCH_PARAM = "q"
    PAGE_PARAM = "page"

    def extract(self, request: HttpRequest) -> CourseQueryFilter:
        difficulty = request.GET.get(self.DIFFICULTY_PARAM, "").strip() or None
        search = request.GET.get(self.SEARCH_PARAM, "").strip() or None
        querystring = self._clean_querystring(request)

        return CourseQueryFilter(
            difficulty=difficulty,
            search=search,
            querystring=querystring,
        )

    def _clean_querystring(self, request: HttpRequest) -> str:
        """Strip the ``page`` param so pagination links stay filter-aware."""
        qp = request.GET.copy()
        qp.pop(self.PAGE_PARAM, None)
        return qp.urlencode()


class CoursePageBuilder:
    """
    Single responsibility: build the course list for a given grade-subject
    and quarter, applying the active filters.

    Open for extension — override ``build`` to add caching, alternative
    data sources, or annotation layers without touching the view.

    Wraps ``build_grade_subject_courses_page`` so the view never imports
    the query function directly (DIP).
    """

    def build(
        self,
        grade_subject: object,
        quarter: str | None,
        user: object,
        filters: CourseQueryFilter,
    ) -> list:

        return build_grade_subject_courses_page(
            grade_subject=grade_subject,
            quarter=quarter,
            user=user,
            difficulty=filters.difficulty,
            search=filters.search,
        )


class TermLabelResolver:
    """
    Single responsibility: resolve a Term key into its human-readable
    display label.

    Avoids repeating ``dict(Term.choices).get(term, term or "")``
    across multiple views.
    """

    def __init__(self, choices: list[tuple]) -> None:
        self._map: dict = dict(choices)

    def resolve(self, term: str | None) -> str:
        if term is None:
            return ""
        return self._map.get(term, term)


class CoursesByQuarterCrumbBuilder(BreadcrumbBuilder):
    """
    5-crumb chain: Home → Levels → Level → Grade(+specialty) → Subject → Quarter.

    Extends BreadcrumbBuilder (OCP). The grade URL specialty-param
    construction is the same pattern as GradeSubjectCrumbBuilder —
    lives here, not in the view.
    """

    CRUMB_DEFINITIONS: list[dict] = [
        {"label": _("Home"), "url_name": "pages:landing", "icon": "fas fa-home"},
        {"label": _("Levels"), "url_name": "curriculum:level:level-list"},
    ]

    def build_for_courses_by_quarter(
        self,
        grade_subject: object,
        quarter_display: str,
    ) -> list[dict]:
        gs = grade_subject
        grade = gs.grade
        level = grade.level
        specialty = gs.specialty

        crumbs = self.build()

        crumbs.append(
            {
                "label": self._display_name(level),
                "url": reverse(
                    "curriculum:level:level-detail",
                    kwargs={"pk": level.pk},
                ),
            }
        )

        grade_url = reverse(
            "curriculum:grade:grade-detail",
            kwargs={"pk": grade.pk},
        )
        if specialty:
            grade_url += f"?specialty={specialty.pk}"

        grade_label = grade.short_name
        if specialty:
            grade_label = f"{grade_label} | {specialty.short_name}"

        crumbs.append({"label": grade_label, "url": grade_url})

        crumbs.append(
            {
                "label": gs.subject.short_name,
                "url": reverse(
                    "curriculum:grade-subject:grade-subject-detail",
                    kwargs={"pk": gs.pk},
                ),
            }
        )

        crumbs.append(
            {
                "label": _("Courses — %(quarter)s") % {"quarter": quarter_display},
                "url": None,
            }
        )

        return crumbs


@dataclass(frozen=True)
class QuizFilter:
    """
    Immutable value object carrying all active filter params
    for the quiz list page.
    """

    q: str | None
    course_id: str | None
    teacher_id: str | None
    auto_grade: str | None  # "1" | "0" | None
    querystring: str  # pagination-stripped


class QuizFilterExtractor:
    """
    Single responsibility: extract and clean the 4 quiz filter params
    from the request into a QuizFilter value object.

    Open for extension — subclass and override ``extract`` to add new
    params (e.g. ``difficulty``, ``tag``) without touching the view.
    """

    def extract(self, request: HttpRequest) -> QuizFilter:
        return QuizFilter(
            q=request.GET.get("q", "").strip() or None,
            course_id=request.GET.get("course", "").strip() or None,
            teacher_id=request.GET.get("teacher", "").strip() or None,
            auto_grade=request.GET.get("auto_gradable", "").strip() or None,
            querystring=self._clean_querystring(request),
        )

    @staticmethod
    def _clean_querystring(request: HttpRequest) -> str:
        qp = request.GET.copy()
        qp.pop("page", None)
        return qp.urlencode()


class QuizQuerysetBuilder:
    """
    Single responsibility: build the filtered, annotated Quiz queryset.

    All ORM logic lives here — the view never imports Quiz or Count.
    Open for extension — override ``_apply_filters`` to add new filter
    conditions without touching the base queryset construction.
    """

    def build(self, grade_subject: object, filters: QuizFilter) -> QuerySet:
        from apps.assessment.models import Quiz

        qs = (
            Quiz.objects.filter(
                grade_subject=grade_subject,
                is_published=True,
            )
            .select_related("created_by", "course")
            .annotate(
                questions_count=Count("quiz_questions", distinct=True),
            )
            .order_by("-created_at")
        )

        return self._apply_filters(qs, filters)

    def _apply_filters(self, qs: QuerySet, filters: QuizFilter) -> QuerySet:
        if filters.q:
            qs = qs.filter(
                Q(title__icontains=filters.q) | Q(description__icontains=filters.q)
            )

        if filters.course_id:
            qs = qs.filter(course_id=filters.course_id)

        if filters.teacher_id:
            qs = qs.filter(created_by_id=filters.teacher_id)

        if filters.auto_grade == "1":
            qs = qs.filter(is_auto_gradable_snapshot=True)
        elif filters.auto_grade == "0":
            qs = qs.filter(is_auto_gradable_snapshot=False)

        return qs


@dataclass(frozen=True)
class QuizSidebarData:
    """Value object bundling both sidebar queries."""

    courses: object  # QuerySet
    teachers: object  # QuerySet


class QuizSidebarProvider:
    """
    Single responsibility: fetch the two sidebar filter datasets —
    courses and teachers — scoped to the given grade_subject.

    Both queries use ``.only()`` to avoid over-fetching.
    """

    def fetch(self, grade_subject: object) -> QuizSidebarData:
        from apps.accounts.models import CustomUser
        from apps.content.models import Course

        courses = (
            Course.objects.filter(grade_subject=grade_subject)
            .only("id", "title")
            .order_by("title")
        )

        teachers = (
            CustomUser.objects.filter(
                created_quizzes__grade_subject=grade_subject,
                created_quizzes__is_published=True,
            )
            .distinct()
            .only("id", "first_name", "last_name")
        )

        return QuizSidebarData(courses=courses, teachers=teachers)


class QuizzesCrumbBuilder(BreadcrumbBuilder):
    """
    6-crumb chain: Home → Levels → Level → Grade → Subject → Quizzes.
    Identical specialty-param pattern as CoursesByQuarterCrumbBuilder.
    """

    CRUMB_DEFINITIONS: list[dict] = [
        {"label": _("Home"), "url_name": "pages:landing", "icon": "fas fa-home"},
        {"label": _("Levels"), "url_name": "curriculum:level:level-list"},
    ]

    def build_for_quizzes(self, grade_subject: object) -> list[dict]:
        gs = grade_subject
        grade = gs.grade
        level = grade.level
        specialty = gs.specialty

        crumbs = self.build()

        crumbs.append(
            {
                "label": self._display_name(level),
                "url": reverse(
                    "curriculum:level:level-detail",
                    kwargs={"pk": level.pk},
                ),
            }
        )

        grade_url = reverse(
            "curriculum:grade:grade-detail",
            kwargs={"pk": grade.pk},
        )
        if specialty:
            grade_url += f"?specialty={specialty.pk}"

        grade_label = grade.short_name
        if specialty:
            grade_label = f"{grade_label} | {specialty.short_name}"

        crumbs.append({"label": grade_label, "url": grade_url})

        crumbs.append(
            {
                "label": gs.subject.short_name,
                "url": reverse(
                    "curriculum:grade-subject:grade-subject-detail",
                    kwargs={"pk": gs.pk},
                ),
            }
        )

        crumbs.append({"label": _("Quizzes"), "url": None})

        return crumbs


@dataclass(frozen=True)
class ResourceFilter:
    """
    Immutable value object carrying all 8 active filter params
    for the resource list page.

    Also carries the resolved active_term — URL kwarg takes priority
    over GET param, so that logic lives here, not scattered across
    get_queryset and get_context_data.
    """

    q: str | None
    difficulty: str | None
    term: str | None  # from GET param only
    resource_type: str | None  # from GET param only
    has_solution: str | None  # "1" | "0" | None
    is_free: str | None  # "1" | "0" | None
    course: str | None
    teacher: str | None
    querystring: str  # pagination-stripped
    active_term: str | None  # resolved: url_kwarg > GET param > None
    active_resource_type: str | None  # resolved: url_kwarg > GET param > None


class ResourceFilterExtractor:
    """
    Single responsibility: extract, clean, and package all 8 GET params
    plus URL kwarg overrides into a ResourceFilter value object.

    The URL kwarg priority logic (current_term > GET term) lives here
    — not duplicated across get_queryset and get_context_data.

    Open for extension — subclass and override ``extract`` to add new
    filter params without touching the view or queryset builder.
    """

    def extract(
        self,
        request: HttpRequest,
        current_term: str | None,
        resource_slug: str | None,
    ) -> ResourceFilter:
        GET = request.GET

        q = GET.get("q", "").strip() or None
        difficulty = GET.get("difficulty", "").strip() or None
        term = GET.get("term", "").strip() or None
        resource_type = GET.get("resource_type", "").strip() or None
        has_solution = GET.get("has_solution", "").strip() or None
        is_free = GET.get("is_free", "").strip() or None
        course = GET.get("course", "").strip() or None
        teacher = GET.get("teacher", "").strip() or None

        qp = GET.copy()
        qp.pop("page", None)

        return ResourceFilter(
            q=q,
            difficulty=difficulty,
            term=term,
            resource_type=resource_type,
            has_solution=has_solution,
            is_free=is_free,
            course=course,
            teacher=teacher,
            querystring=qp.urlencode(),
            active_term=current_term or term,
            active_resource_type=resource_slug or resource_type,
        )


class ResourceQuerysetBuilder:
    """
    Single responsibility: build the filtered Resource queryset.

    All ORM logic lives here — the view never imports Resource, Q,
    ResourceType, or ResourceStatus directly.

    Open for extension — override ``_apply_filters`` to add new
    conditions without touching the base queryset construction.
    """

    def build(
        self,
        grade_subject: object,
        filters: ResourceFilter,
    ) -> QuerySet:
        from apps.content.choices import ResourceStatus, ResourceType
        from apps.content.models import Resource

        qs = (
            Resource.objects.filter(
                grade_subject=grade_subject,
                resource_type__in=ResourceType.get_subject_values(),
                status=ResourceStatus.PUBLISHED,
            )
            .select_related("created_by", "course")
            .prefetch_related("tags")
            .order_by("term", "resource_type", "order")
        )

        return self._apply_filters(qs, filters)

    def _apply_filters(self, qs: QuerySet, filters: ResourceFilter) -> QuerySet:
        if filters.active_term:
            qs = qs.filter(term=filters.active_term)

        if filters.active_resource_type:
            qs = qs.filter(resource_type=filters.active_resource_type)

        if filters.q:
            qs = qs.filter(
                Q(title__icontains=filters.q)
                | Q(content__icontains=filters.q)
                | Q(tags__name__icontains=filters.q)
            ).distinct()

        if filters.difficulty:
            qs = qs.filter(difficulty=filters.difficulty)

        if filters.has_solution == "1":
            qs = qs.filter(has_solution=True)
        elif filters.has_solution == "0":
            qs = qs.filter(has_solution=False)

        if filters.is_free == "1":
            qs = qs.filter(is_free=True)
        elif filters.is_free == "0":
            qs = qs.filter(is_free=False)

        if filters.course:
            qs = qs.filter(course_id=filters.course)

        if filters.teacher:
            qs = qs.filter(created_by_id=filters.teacher)

        return qs


class ResourceTypeTitleResolver:
    """
    Single responsibility: resolve a resource_slug into a human-readable
    page title.

    Priority:
      1. ResourceType choices label (canonical)
      2. Slug with underscores replaced by spaces, title-cased (fallback)
      3. "Resources" (final fallback when no slug provided)
    """

    def resolve(self, resource_slug: str | None) -> str:
        if not resource_slug:
            return str(_("Resources"))

        from apps.content.choices import ResourceType

        label = dict(ResourceType.get_subject_choices()).get(resource_slug)
        if label:
            return str(label)

        return resource_slug.replace("_", " ").title()


@dataclass(frozen=True)
class ResourceSidebarData:
    courses: object  # QuerySet
    teachers: object  # QuerySet


class ResourceSidebarProvider:
    """
    Single responsibility: fetch courses and teachers scoped to the
    given grade_subject for use in filter sidebar widgets.
    """

    def fetch(self, grade_subject: object) -> ResourceSidebarData:
        from django.contrib.auth import get_user_model

        from apps.content.choices import ResourceStatus
        from apps.content.models import Course

        User = get_user_model()

        courses = (
            Course.objects.filter(
                grade_subject=grade_subject,
                is_active=True,
            )
            .only("id", "title")
            .order_by("title")
        )

        teachers = (
            User.objects.filter(
                resources__grade_subject=grade_subject,
                resources__status=ResourceStatus.PUBLISHED,
            )
            .distinct()
            .only("id", "first_name", "last_name")
        )

        return ResourceSidebarData(courses=courses, teachers=teachers)


class ResourceTermGrouper:
    """
    Single responsibility: group a resource list by term, preserving
    the canonical Term ordering and skipping empty terms.

    Returns a list of (term_value, term_label, resources) tuples —
    the same contract the template already expects.
    """

    def group(self, resources, term_choices: list[tuple]) -> list[tuple]:
        term_order = [t[0] for t in term_choices]
        grouped: dict = {term: [] for term in term_order}

        for resource in resources:
            if resource.term in grouped:
                grouped[resource.term].append(resource)

        from ..models import Term

        return [
            (term, Term(term).label, grouped[term])
            for term in term_order
            if grouped[term]
        ]


class ResourceListCrumbBuilder(BreadcrumbBuilder):
    """
    6-crumb chain: Home → Levels → Level → Grade(+specialty) → Subject → ResourceType.
    """

    CRUMB_DEFINITIONS: list[dict] = [
        {"label": _("Home"), "url_name": "pages:landing", "icon": "fas fa-home"},
        {"label": _("Levels"), "url_name": "curriculum:level:level-list"},
    ]

    def build_for_resources(
        self,
        grade_subject: object,
        resource_type_title: str,
    ) -> list[dict]:
        gs = grade_subject
        grade = gs.grade
        level = grade.level
        specialty = gs.specialty

        crumbs = self.build()

        crumbs.append(
            {
                "label": self._display_name(level),
                "url": reverse(
                    "curriculum:level:level-detail",
                    kwargs={"pk": level.pk},
                ),
            }
        )

        grade_url = reverse(
            "curriculum:grade:grade-detail",
            kwargs={"pk": grade.pk},
        )
        if specialty:
            grade_url += f"?specialty={specialty.pk}"

        grade_label = grade.short_name
        if specialty:
            grade_label = f"{grade_label} | {specialty.short_name}"

        crumbs.append({"label": grade_label, "url": grade_url})

        crumbs.append(
            {
                "label": gs.subject.short_name,
                "url": reverse(
                    "curriculum:grade-subject:grade-subject-detail",
                    kwargs={"pk": gs.pk},
                ),
            }
        )

        crumbs.append({"label": resource_type_title, "url": None})

        return crumbs
