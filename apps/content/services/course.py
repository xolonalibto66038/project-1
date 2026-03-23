import logging
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from django.db import transaction
from django.db.models import Count, Q, QuerySet
from django.http import Http404, HttpRequest
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from apps.curriculum.services.level import BreadcrumbBuilder

from ..selectors import get_or_create_course_progress

logger = logging.getLogger(__name__)


def record_course_visit(student, course):
    """
    Creates or updates ContentProgress for a student visiting a course.
    Idempotent — safe to call on every GET.
    Returns the ContentProgress instance.
    """
    progress, created = get_or_create_course_progress(student, course)

    if not created:
        # bump first_viewed_at only on first visit; just return on repeat
        pass

    return progress


@runtime_checkable
class CourseVisitRecorderProtocol(Protocol):
    """
    LSP boundary for visit recording.
    Swap in NoOpCourseVisitRecorder for tests — no DB, no transaction.
    """

    def record(self, user: object, course: object) -> None: ...


class CourseVisitRecorder:
    """
    Single responsibility: record a student's visit to a course,
    wrapped in an atomic transaction.

    Guards against non-students being passed in — safe to call
    unconditionally from the view after the student check.
    """

    def record(self, user: object, course: object) -> None:

        try:
            with transaction.atomic():
                record_course_visit(user, course)
        except Exception:
            logger.exception(
                "CourseVisitRecorder: failed to record visit " "for user=%s course=%s.",
                getattr(user, "pk", "?"),
                getattr(course, "pk", "?"),
            )


class NoOpCourseVisitRecorder:
    """
    LSP-compliant stub — satisfies the protocol, does nothing.
    Use in unit tests to avoid DB writes.
    """

    def record(self, user: object, course: object) -> None:
        pass


class StudentGradeMatchChecker:
    """
    Single responsibility: determine whether an authenticated student
    is enrolled in the same grade as a given course.

    Open for extension — override ``is_matching`` to support teacher
    previews, admin overrides, or multi-grade enrolment without
    touching the view.
    """

    def is_matching(self, user: object, course: object) -> bool:
        if not (user.is_authenticated and getattr(user, "is_student", False)):
            return False

        try:
            student_grade = getattr(user.student_profile, "grade", None)
        except Exception:
            logger.debug(
                "StudentGradeMatchChecker: could not read grade " "for user %s.",
                getattr(user, "pk", "?"),
            )
            return False

        gs = getattr(course, "effective_grade_subject", None)
        course_grade = gs.grade if gs else None

        return (
            student_grade is not None
            and course_grade is not None
            and student_grade == course_grade
        )


class CourseProgressProvider:
    """
    Single responsibility: fetch progress data for a student on a course.

    Returns None when the user is not a matching student — the view
    passes the result directly to the template without further branching.

    Open for extension — override ``get_progress`` to add caching or
    alternative progress sources.
    """

    def get_progress(
        self,
        user: object,
        course: object,
        is_matching_student: bool,
    ) -> object | None:
        if not is_matching_student:
            return None

        from ..selectors import get_course_progress

        return get_course_progress(user, course)


class CourseCrumbBuilder(BreadcrumbBuilder):
    """
    Dynamic crumb chain for a course detail page.

    Chain: Home → Levels → Level → Grade(+specialty) → Subject
           → [Chapter (optional)] → Course title

    Wraps ``resolve_course_breadcrumb`` — does not replace it.
    The existing function produces the level/grade/subject/chapter
    dict; this class turns it into the crumb list the template expects.
    """

    CRUMB_DEFINITIONS: list[dict] = [
        {"label": _("Home"), "url_name": "pages:landing", "icon": "fas fa-home"},
        {"label": _("Levels"), "url_name": "curriculum:level:level-list"},
    ]

    def build_for_course(self, course: object, crumb_data: dict) -> list[dict]:
        level = crumb_data["level"]
        grade = crumb_data["grade"]
        subject = crumb_data["subject"]
        chapter = crumb_data["chapter"]

        gs = getattr(course, "effective_grade_subject", None)
        specialty = gs.specialty if gs else None

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
                "label": subject.short_name,
                "url": reverse(
                    "curriculum:grade-subject:grade-subject-detail",
                    kwargs={"pk": gs.pk},
                ),
            }
        )

        if chapter:
            crumbs.append({"label": chapter.title, "url": None})

        crumbs.append({"label": course.title, "url": None})

        return crumbs


class ResourceTypeConfigResolver:
    """
    Single responsibility: resolve a resource_slug into its config dict,
    raising Http404 for unknown slugs.

    Wraps RESOURCE_TYPE_CONFIG — the view never imports the dict directly
    (DIP). Swap in a test subclass to inject arbitrary configs.

    Open for extension — override ``resolve`` to add slug aliases,
    permission checks, or feature-flag gating per resource type.
    """

    def resolve(self, slug: str | None) -> dict:
        from ..consts import RESOURCE_TYPE_CONFIG

        if not slug:
            raise Http404(_("No resource type specified."))

        config = RESOURCE_TYPE_CONFIG.get(slug)
        if not config:
            raise Http404(_("Unknown resource type: %(slug)s") % {"slug": slug})

        return config


@dataclass(frozen=True)
class CourseResourceFilter:
    """
    Immutable value object for the 3 course resource filter params.
    """

    q: str | None
    difficulty: str | None
    has_solution: str | None  # "1" | "0" | None
    completed: str | None  # "1" | "0" | None
    querystring: str


# Defined here — not inline in the view (OCP: extend without touching view)
HAS_SOLUTION_CHOICES: list[tuple] = [
    ("", _("— All —")),
    ("1", _("With Solution")),
    ("0", _("Without Solution")),
]


class CourseResourceFilterExtractor:
    """
    Single responsibility: extract and clean the 4 course resource
    filter params from the request into a CourseResourceFilter.

    Open for extension — subclass and override ``extract`` to add
    new params without touching the view.
    """

    def extract(self, request: HttpRequest) -> CourseResourceFilter:
        return CourseResourceFilter(
            q=request.GET.get("q", "").strip() or None,
            difficulty=request.GET.get("difficulty", "").strip() or None,
            has_solution=request.GET.get("has_solution", "").strip() or None,
            completed=request.GET.get("completed", "").strip() or None,
            querystring=self._clean_querystring(request),
        )

    @staticmethod
    def _clean_querystring(request: HttpRequest) -> str:
        qp = request.GET.copy()
        qp.pop("page", None)
        return qp.urlencode()


class CourseResourceQuerysetBuilder:
    """
    Single responsibility: delegate to get_course_resources with the
    resolved config and filters.

    The view never calls get_course_resources directly (DIP).
    Open for extension — override ``build`` to add caching or
    annotation layers.
    """

    def build(
        self,
        course: object,
        config: dict,
        request_GET,
        user: object,
    ):
        from ..selectors import get_course_resources

        return get_course_resources(
            course=course,
            resource_type=config["resource_type"],
            filters=request_GET,
            user=user,
        )


class CourseResourceCrumbBuilder(BreadcrumbBuilder):
    """
    Chain: Home → Levels → Level → Grade(+specialty)
           → Subject → [Chapter (optional)] → Course → Resource type title

    Identical specialty-param and optional-chapter patterns as
    CourseCrumbBuilder — reuses _display_name from base.
    """

    CRUMB_DEFINITIONS: list[dict] = [
        {"label": _("Home"), "url_name": "pages:landing", "icon": "fas fa-home"},
        {"label": _("Levels"), "url_name": "curriculum:level:level-list"},
    ]

    def build_for_course_resources(
        self,
        course: object,
        config: dict,
        level: object,
        grade: object,
        subject: object,
    ) -> list[dict]:
        gs = getattr(course, "effective_grade_subject", None)
        specialty = gs.specialty if gs else None
        chapter = getattr(course, "chapter", None)

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
                "label": subject.short_name,
                "url": reverse(
                    "curriculum:grade-subject:grade-subject-detail",
                    kwargs={"pk": gs.pk},
                ),
            }
        )

        if chapter:
            crumbs.append({"label": chapter.title, "url": None})

        crumbs.append(
            {
                "label": course.title,
                "url": reverse(
                    "content:course:course-detail",
                    kwargs={"pk": course.pk},
                ),
            }
        )

        crumbs.append({"label": config["title"], "url": None})

        return crumbs


@dataclass(frozen=True)
class VideoFilter:
    q: str | None
    teacher_id: str | None
    video_pk: str | None  # selected video param
    querystring: str  # "video" param stripped


class VideoFilterExtractor:
    """
    Single responsibility: extract and clean all video page params.

    Strips ``video`` from the querystring so it doesn't duplicate
    when the user selects a different video — that logic lives here,
    not in the view.
    """

    def extract(self, request: HttpRequest) -> VideoFilter:
        qp = request.GET.copy()
        qp.pop("video", None)

        return VideoFilter(
            q=request.GET.get("q", "").strip() or None,
            teacher_id=request.GET.get("teacher", "").strip() or None,
            video_pk=request.GET.get("video", "").strip() or None,
            querystring=qp.urlencode(),
        )


class VideoStudentAnnotator:
    """
    Single responsibility: annotate a video queryset with all four
    student-specific fields — is_seen, is_bookmarked, watched_seconds,
    duration_seconds.

    All inline imports live here, not in the view. Open for extension —
    override ``annotate`` to add new per-student fields (e.g. rating)
    without touching the view or the queryset builder.
    """

    def annotate(self, qs: QuerySet, user: object) -> QuerySet:
        from django.contrib.contenttypes.models import ContentType
        from django.db.models import Exists, IntegerField, OuterRef, Subquery

        from apps.content.models import VideoResource
        from apps.feedback.models import Bookmark
        from apps.progress.models import ContentProgress, VideoWatchProgress

        ct = ContentType.objects.get_for_model(VideoResource)

        return qs.annotate(
            is_seen=Exists(
                ContentProgress.objects.filter(
                    student=user,
                    content_type=ct,
                    object_id=OuterRef("pk"),
                    is_completed=True,
                )
            ),
            is_bookmarked=Exists(
                Bookmark.objects.filter(
                    student=user,
                    content_type=ct,
                    object_id=OuterRef("pk"),
                    active=True,
                )
            ),
            watched_seconds=Subquery(
                VideoWatchProgress.objects.filter(
                    student=user,
                    video=OuterRef("pk"),
                ).values("watched_seconds")[:1],
                output_field=IntegerField(),
            ),
            duration_seconds=Subquery(
                VideoWatchProgress.objects.filter(
                    student=user,
                    video=OuterRef("pk"),
                ).values("duration_seconds")[:1],
                output_field=IntegerField(),
            ),
        )


class VideoQuerysetBuilder:
    """
    Single responsibility: build the filtered (and optionally annotated)
    video queryset for a course.

    Delegates student annotation to VideoStudentAnnotator — the two
    concerns (filtering and annotation) stay separate and independently
    testable.
    """

    def __init__(
        self,
        annotator: VideoStudentAnnotator | None = None,
    ) -> None:
        self._annotator = annotator or VideoStudentAnnotator()

    def build(
        self,
        course: object,
        filters: VideoFilter,
        is_student: bool,
        user: object,
    ) -> QuerySet:
        qs = course.videos.filter(is_active=True).order_by("order")

        if filters.q:
            qs = qs.filter(
                Q(title__icontains=filters.q) | Q(tags__name__icontains=filters.q)
            ).distinct()

        if filters.teacher_id:
            qs = qs.filter(created_by_id=filters.teacher_id)

        if is_student:
            qs = self._annotator.annotate(qs, user)

        return qs


class CurrentVideoSelector:
    """
    Single responsibility: select the active video from the queryset.

    Priority:
      1. ``video`` GET param matching a video in the queryset
      2. First video in the queryset
      3. None (empty queryset)
    """

    def select(self, videos: QuerySet, video_pk: str | None) -> object | None:
        if video_pk:
            match = videos.filter(pk=video_pk).first()
            if match:
                return match
        return videos.first()


class VideoTeacherProvider:
    """
    Single responsibility: fetch teachers who have active videos
    on a given course, for the filter sidebar dropdown.
    """

    def fetch(self, course: object) -> object:
        from django.contrib.auth import get_user_model

        User = get_user_model()

        return (
            User.objects.filter(
                videos__course=course,
                videos__is_active=True,
            )
            .distinct()
            .only("id", "first_name", "last_name")
        )


class CourseVideosCrumbBuilder(BreadcrumbBuilder):
    """
    Null-safe chain: every node (level, grade, gs, chapter) is
    optional — the course may not have a full curriculum chain
    attached. Guards with ``if x:`` before appending each crumb.

    Chain: Home → Levels → [Level] → [Grade(+specialty)]
           → [Subject] → [Chapter] → Course → Videos
    """

    CRUMB_DEFINITIONS: list[dict] = [
        {"label": _("Home"), "url_name": "pages:landing", "icon": "fas fa-home"},
        {"label": _("Levels"), "url_name": "curriculum:level:level-list"},
    ]

    def build_for_videos(self, course: object) -> list[dict]:
        gs = getattr(course, "effective_grade_subject", None)
        grade = gs.grade if gs else None
        subject = gs.subject if gs else None
        level = grade.level if grade else None
        specialty = gs.specialty if gs else None
        chapter = getattr(course, "chapter", None)

        crumbs = self.build()

        if level:
            crumbs.append(
                {
                    "label": self._display_name(level),
                    "url": reverse(
                        "curriculum:level:level-detail",
                        kwargs={"pk": level.pk},
                    ),
                }
            )

        if grade:
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

        if gs and subject:
            crumbs.append(
                {
                    "label": subject.short_name,
                    "url": reverse(
                        "curriculum:grade-subject:grade-subject-detail",
                        kwargs={"pk": gs.pk},
                    ),
                }
            )

        if chapter:
            crumbs.append({"label": chapter.title, "url": None})

        crumbs.append(
            {
                "label": course.title,
                "url": reverse(
                    "content:course:course-detail",
                    kwargs={"pk": course.pk},
                ),
            }
        )

        crumbs.append({"label": _("Videos"), "url": None})

        return crumbs


@dataclass(frozen=True)
class CourseQuizFilter:
    q: str | None
    teacher_id: str | None
    auto_grade: str | None  # "1" | "0" | None
    term: str | None
    querystring: str


class CourseQuizFilterExtractor:
    """
    Single responsibility: extract and clean the 4 quiz filter params.
    Open for extension — subclass to add params without touching the view.
    """

    def extract(self, request: HttpRequest) -> CourseQuizFilter:
        GET = request.GET
        qp = GET.copy()
        qp.pop("page", None)

        return CourseQuizFilter(
            q=GET.get("q", "").strip() or None,
            teacher_id=GET.get("teacher", "").strip() or None,
            auto_grade=GET.get("auto_gradable", "").strip() or None,
            term=GET.get("term", "").strip() or None,
            querystring=qp.urlencode(),
        )


class CourseQuizQuerysetBuilder:
    """
    Single responsibility: build the filtered, user-annotated Quiz
    queryset for a course detail page.

    The user-scoped ``user_attempts_count`` annotation lives here —
    not inline in the view. Open for extension — override
    ``_apply_filters`` to add new conditions.
    """

    def build(
        self,
        course: object,
        filters: CourseQuizFilter,
        user: object,
    ) -> QuerySet:
        from apps.assessment.models import Quiz

        qs = (
            Quiz.objects.filter(
                course=course,
                is_published=True,
            )
            .select_related("created_by")
            .annotate(
                questions_count=Count("quiz_questions", distinct=True),
                user_attempts_count=Count(
                    "quiz_attempts",
                    filter=Q(quiz_attempts__student=user),
                    distinct=True,
                ),
            )
            .order_by("-created_at")
        )

        return self._apply_filters(qs, filters)

    def _apply_filters(self, qs: QuerySet, filters: CourseQuizFilter) -> QuerySet:
        if filters.q:
            qs = qs.filter(
                Q(title__icontains=filters.q) | Q(description__icontains=filters.q)
            )
        if filters.teacher_id:
            qs = qs.filter(created_by_id=filters.teacher_id)
        if filters.auto_grade == "1":
            qs = qs.filter(is_auto_gradable_snapshot=True)
        elif filters.auto_grade == "0":
            qs = qs.filter(is_auto_gradable_snapshot=False)
        if filters.term:
            qs = qs.filter(term=filters.term)
        return qs


class CourseQuizzesCrumbBuilder(CourseVideosCrumbBuilder):
    """
    Identical null-safe chain as CourseVideosCrumbBuilder — only the
    terminal label differs ("Quizzes" vs "Videos").

    Extends rather than duplicates — OCP: closed for modification,
    open for the one-label difference.
    """

    def build_for_quizzes(self, course: object) -> list[dict]:
        crumbs = self.build_for_videos(course)
        # Replace the terminal "Videos" crumb with "Quizzes"
        if crumbs:
            crumbs[-1] = {"label": _("Quizzes"), "url": None}
        return crumbs


class CourseCompletionToggler:
    """
    Single responsibility: toggle the completion state of a course
    for a given student.

    Returns the new state so the caller can dispatch an appropriate
    message without re-reading the object.
    """

    def toggle(self, user: object, course: object) -> bool:
        """
        Toggle completion for ``user`` on ``course``.

        Returns True  if the course is now marked completed.
        Returns False if the course is now marked incomplete.
        """
        from django.contrib.contenttypes.models import ContentType

        from apps.progress.models import ContentProgress

        content_type = ContentType.objects.get_for_model(course.__class__)

        progress, _ = ContentProgress.objects.get_or_create(
            student=user,
            content_type=content_type,
            object_id=course.pk,
        )

        if progress.is_completed:
            progress.mark_incomplete()
            return False
        else:
            progress.mark_completed()
            return True
