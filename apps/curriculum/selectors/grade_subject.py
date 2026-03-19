from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, Q

from apps.content.choices import ResourceStatus, ResourceType, Term
from apps.content.models import Course, Resource
from apps.progress.models import ContentProgress

from ..models import GradeSubject


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
            quizzes_count=Count(
                "quizzes",
                filter=Q(quizzes__is_published=True),
                distinct=True,
            ),
            # quizzes_count=Quiz.objects.filter(
            #     is_published=True,
            # )
            # .filter(
            #     Q(course__grade_subject_id=pk, course__term=term)
            #     | Q(course__chapter__grade_subject_id=pk, course__chapter__term=term)
            # )
            # .distinct()
            # .count(),
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


def get_grade_subject_courses_by_quarter(
    grade_subject, quarter: str, user=None, difficulty=None, search=None
):
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
    # ── Filters ──────────────────────────────────────────────────────────
    if difficulty:
        qs = qs.filter(difficulty=difficulty)

    if search:
        qs = qs.filter(Q(title__icontains=search) | Q(description__icontains=search))

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


def get_grade_subject_counts_by_quarter(pk):
    """
    Returns counts for all resource types grouped by term.
    Shape: {
        'first':  {courses, tests, exams, past_papers, mock_exams, textbooks, foreign_books, study_guides},
        'second': {...},
        'third':  {...},
    }
    """
    result = {}

    for term in Term.values:
        gs = get_grade_subject_by_pk(pk=pk, term=term)
        result[term] = {
            "courses": gs.courses_count,
            "quizzes": gs.quizzes_count,
            "test": gs.tests_count,
            "exam": gs.exams_count,
            "past_paper": gs.past_papers_count,
            "mock_exam": gs.mock_exams_count,
            "textbook": gs.textbooks_count,
            "foreign_book": gs.foreign_books_count,
            "study_guide": gs.study_guides_count,
        }

    return result


def get_grade_subject_counts(pk):
    """
    Returns total counts of courses, quizzes, and resources
    for a given GradeSubject pk.

    Courses are counted from both:
      - direct FK (grade_subject_id = pk)
      - via chapter (chapter__grade_subject_id = pk)
    """
    from apps.assessment.models import Quiz  # adjust import to your app
    from apps.content.models import Course, Resource

    course_count = Course.objects.filter(
        Q(grade_subject_id=pk) | Q(chapter__grade_subject_id=pk),
        is_active=True,
    ).count()

    resource_count = Resource.objects.filter(
        grade_subject_id=pk,
        is_active=True,
    ).count()

    quiz_count = Quiz.objects.filter(
        grade_subject_id=pk,
        is_published=True,
    ).count()

    return {
        "course_count": course_count,
        "resource_count": resource_count,
        "quiz_count": quiz_count,
    }


def get_grade_subject_resources(grade_subject, resource_type, filters=None, user=None):
    """
    Generic resource selector for any subject resource type.
    Supports filters: q, difficulty, term.
    Subject resources are NOT linked to a course — they belong to Subject directly.
    """
    qs = Resource.objects.filter(
        grade_subject=grade_subject,
        resource_type=resource_type,
        status=ResourceStatus.PUBLISHED,
    ).order_by("term", "order")

    if filters:
        q = filters.get("q", "").strip()
        difficulty = filters.get("difficulty", "")
        term = filters.get("term", "")

        if q:
            qs = qs.filter(title__icontains=q)
        if difficulty:
            qs = qs.filter(difficulty=difficulty)
        if term:
            qs = qs.filter(term=term)

    return qs


def get_course_counts_for_grade_subjects(grade_subject_ids):
    return dict(
        Course.objects.filter(
            grade_subject_id__in=grade_subject_ids,
            is_active=True,
        )
        .values("grade_subject_id")
        .annotate(count=Count("id"))
        .values_list("grade_subject_id", "count")
    )


def get_resource_counts_for_grade_subjects(grade_subject_ids):
    """Direct subject-level resources (tests, exams, etc.)"""
    return dict(
        Resource.objects.filter(
            grade_subject_id__in=grade_subject_ids,
            status="published",
        )
        .values("grade_subject_id")
        .annotate(count=Count("id"))
        .values_list("grade_subject_id", "count")
    )


def get_grade_subjects_for_grade(grade, specialty=None):
    """
    Returns GradeSubject rows for this grade with subject pre-fetched.
    Used to build the subject list on the grade detail page.
    """
    qs = (
        GradeSubject.objects.filter(grade=grade, is_active=True)
        .select_related("subject", "specialty")
        .order_by("subject__name")
    )

    if specialty is not None:
        qs = qs.filter(specialty=specialty)
    else:
        qs = qs.filter(specialty__isnull=True)

    return qs


def get_course_resource_counts_for_grade_subjects(grade_subject_ids):
    """Resources attached to courses under these subjects."""
    return dict(
        Resource.objects.filter(
            course__grade_subject_id__in=grade_subject_ids,
            course__is_active=True,
            status="published",
        )
        .values("course__grade_subject_id")
        .annotate(count=Count("id"))
        .values_list("course__grade_subject_id", "count")
    )
