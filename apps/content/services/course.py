import logging
from typing import Protocol, runtime_checkable

from django.db import transaction
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
