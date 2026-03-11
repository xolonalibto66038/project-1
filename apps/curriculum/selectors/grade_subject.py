from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, Q

from apps.content.choices import ResourceType
from apps.content.models import Course
from apps.progress.models import ContentProgress

from ..models import GradeSubject
from .subject import resolve_term


def get_grade_subject_by_pk(pk, term=None):
    term_filter = Q(courses__term=term) if term else Q()
    res_term_filter = Q(resources__term=term) if term else Q()

    return (
        GradeSubject.objects.select_related(
            "grade",
            "grade__level",
            "subject",
            "subject__level",
            "specialty",
        )
        .annotate(
            # ── Courses ──
            courses_count=Count(
                "courses",
                filter=Q(courses__is_active=True) & term_filter,
                distinct=True,
            ),
            # ── Course resources (via course) ──
            lessons_count=Count(
                "courses__resources",
                filter=Q(
                    courses__resources__resource_type=ResourceType.LESSON,
                    courses__resources__status="published",
                )
                & (Q(courses__resources__term=term) if term else Q()),
                distinct=True,
            ),
            exercises_count=Count(
                "courses__resources",
                filter=Q(
                    courses__resources__resource_type=ResourceType.EXERCISE,
                    courses__resources__status="published",
                )
                & (Q(courses__resources__term=term) if term else Q()),
                distinct=True,
            ),
            homeworks_count=Count(
                "courses__resources",
                filter=Q(
                    courses__resources__resource_type=ResourceType.HOMEWORK,
                    courses__resources__status="published",
                )
                & (Q(courses__resources__term=term) if term else Q()),
                distinct=True,
            ),
            summaries_count=Count(
                "courses__resources",
                filter=Q(
                    courses__resources__resource_type=ResourceType.SUMMARY,
                    courses__resources__status="published",
                )
                & (Q(courses__resources__term=term) if term else Q()),
                distinct=True,
            ),
            notes_count=Count(
                "courses__resources",
                filter=Q(
                    courses__resources__resource_type=ResourceType.NOTES,
                    courses__resources__status="published",
                )
                & (Q(courses__resources__term=term) if term else Q()),
                distinct=True,
            ),
            series_count=Count(
                "courses__resources",
                filter=Q(
                    courses__resources__resource_type=ResourceType.SERIES,
                    courses__resources__status="published",
                )
                & (Q(courses__resources__term=term) if term else Q()),
                distinct=True,
            ),
            # ── Subject resources (direct on GradeSubject) ──
            tests_count=Count(
                "resources",
                filter=Q(
                    resources__resource_type=ResourceType.TEST,
                    resources__status="published",
                )
                & res_term_filter,
                distinct=True,
            ),
            exams_count=Count(
                "resources",
                filter=Q(
                    resources__resource_type=ResourceType.EXAM,
                    resources__status="published",
                )
                & res_term_filter,
                distinct=True,
            ),
            past_papers_count=Count(
                "resources",
                filter=Q(
                    resources__resource_type=ResourceType.PAST_PAPER,
                    resources__status="published",
                )
                & res_term_filter,
                distinct=True,
            ),
            mock_exams_count=Count(
                "resources",
                filter=Q(
                    resources__resource_type=ResourceType.MOCK_EXAM,
                    resources__status="published",
                )
                & res_term_filter,
                distinct=True,
            ),
            textbooks_count=Count(
                "resources",
                filter=Q(
                    resources__resource_type=ResourceType.TEXTBOOK,
                    resources__status="published",
                )
                & res_term_filter,
                distinct=True,
            ),
            foreign_books_count=Count(
                "resources",
                filter=Q(
                    resources__resource_type=ResourceType.FOREIGN_BOOK,
                    resources__status="published",
                )
                & res_term_filter,
                distinct=True,
            ),
            study_guides_count=Count(
                "resources",
                filter=Q(
                    resources__resource_type=ResourceType.STUDY_GUIDE,
                    resources__status="published",
                )
                & res_term_filter,
                distinct=True,
            ),
        )
        .get(pk=pk)
    )


def get_grade_subject_courses_by_quarter(grade_subject, quarter: str, user=None):
    """
    Returns all active courses for a subject in a given quarter.

    Covers both:
      - Standalone courses: course.grade_subject = grade_subject, course.term = term
      - Chapter-based courses: course.chapter.grade_subject = grade_subject,
                                course.chapter.term = term

    Annotates each course with:
      - exercises_count
      - resources_count
      - progress_obj (ContentProgress) if user is an authenticated student
    """

    # term = resolve_term(quarter)
    term = quarter

    qs = (
        Course.objects.filter(is_active=True)
        .filter(
            # standalone: direct grade_subject → subject
            Q(
                chapter__isnull=True,
                grade_subject=grade_subject,
                term=term,
            )
            |
            # chapter-based: via chapter → grade_subject → subject
            Q(
                chapter__isnull=False,
                chapter__grade_subject=grade_subject,
                chapter__term=term,
            )
        )
        .select_related("chapter", "grade_subject")
        .annotate(
            exercises_count=Count(
                "resources",
                filter=Q(
                    resources__resource_type=ResourceType.EXERCISE,
                    resources__status="published",
                ),
                distinct=True,
            ),
            resources_count=Count(
                "resources",
                filter=Q(resources__status="published"),
                distinct=True,
            ),
        )
        .order_by("chapter__order", "order")
    )

    # ── Attach progress objects for students ──────────────────────────────
    if (
        user is not None
        and user.is_authenticated
        and getattr(user, "is_student", False)
    ):

        course_ct = ContentType.objects.get_for_model(Course)
        course_ids = list(qs.values_list("id", flat=True))

        progress_map = {
            str(cp.object_id): cp
            for cp in ContentProgress.objects.filter(
                student=user,
                content_type=course_ct,
                object_id__in=course_ids,
            )
        }

        # attach in Python — avoids N+1
        courses = list(qs)
        for course in courses:
            course.progress_obj = progress_map.get(str(course.id))
        return courses

    courses = list(qs)
    for course in courses:
        course.progress_obj = None
    return courses
