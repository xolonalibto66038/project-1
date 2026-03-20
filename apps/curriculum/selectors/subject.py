from collections import defaultdict

from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, Q
from django.http import Http404

from apps.accounts.choices import UserRole
from apps.accounts.models import CustomUser
from apps.content.choices import ResourceStatus, ResourceType
from apps.content.models import Course, Resource
from apps.progress.models import ContentProgress

from ..models import Grade, GradeSubject, Level, Subject


def get_level_by_pk(pk):
    return Level.objects.get(pk=pk)


def get_grade_by_pk(pk):
    return Grade.objects.select_related("level").get(pk=pk)


def get_subject_by_pk(pk):
    return Subject.objects.select_related("level").get(pk=pk)


# def get_grade_subject_by_pk(pk):
#     return GradeSubject.objects.select_related("level").get(pk=pk)


def get_grades_for_level(level):
    return (
        Grade.objects.filter(level=level)
        .annotate(
            subjects_count=Count("grade_subjects__subject", distinct=True),
            specialties_count=Count("specialties", distinct=True),
        )
        .select_related("level")
        .order_by("order", "name")
    )


def get_grade_groups(level):
    grades = get_grades_for_level(level)
    grouped = defaultdict(list)
    for grade in grades:
        grouped[grade.order].append(grade)
    return [
        {"order": order, "grades": grade_list}
        for order, grade_list in sorted(grouped.items())
    ]


def get_subjects_for_grade(grade):
    """
    Returns distinct Subject objects for a grade via GradeSubject.
    """
    return (
        Subject.objects.filter(grade_subjects__grade=grade).distinct().order_by("name")
    )


def get_course_counts_for_subjects(subject_ids):
    return dict(
        Course.objects.filter(
            grade_subject__subject_id__in=subject_ids,
            is_active=True,
        )
        .values("grade_subject__subject_id")
        .annotate(count=Count("id"))
        .values_list("grade_subject__subject_id", "count")
    )


def get_courses_count_for_subject(subject):
    """
    Courses linked to this subject via GradeSubject.
    """
    from apps.content.models.course import Course

    return Course.objects.filter(
        grade_subject__subject=subject,
        is_active=True,
    ).count()


def get_resource_counts_for_subjects(subject_ids):
    """Direct subject-level resources (tests, exams, etc.)"""
    return dict(
        Resource.objects.filter(
            grade_subject_id__in=subject_ids,
            status="published",
        )
        .values("grade_subject_id")
        .annotate(count=Count("id"))
        .values_list("grade_subject_id", "count")
    )


def get_subject_resource_counts(subject):
    """
    Resources attached directly to the subject (tests, exams, past papers…).
    Returns dict: { resource_type: count }
    Also returns total.
    """

    qs = (
        Resource.objects.filter(
            grade_subject__subject=subject,
            status="published",
        )
        .values("resource_type")
        .annotate(count=Count("id"))
    )

    counts = {row["resource_type"]: row["count"] for row in qs}

    return {
        "tests_count": counts.get(ResourceType.TEST, 0),
        "exams_count": counts.get(ResourceType.EXAM, 0),
        "past_papers_count": counts.get(ResourceType.PAST_PAPER, 0),
        "mock_exams_count": counts.get(ResourceType.MOCK_EXAM, 0),
        "textbooks_count": counts.get(ResourceType.TEXTBOOK, 0),
        "foreign_books_count": counts.get(ResourceType.FOREIGN_BOOK, 0),
        "study_guides_count": counts.get(ResourceType.STUDY_GUIDE, 0),
        "subject_resources_count": sum(counts.values()),
    }


def get_course_resource_counts_for_subjects(subject_ids):
    """Resources attached to courses under these subjects."""
    return dict(
        Resource.objects.filter(
            course__grade_subject__subject_id__in=subject_ids,
            course__is_active=True,
            status="published",
        )
        .values("course__grade_subject__subject_id")
        .annotate(count=Count("id"))
        .values_list("course__grade_subject__subject_id", "count")
    )


def get_course_resource_counts_for_subject(subject):
    """
    Resources attached to courses under this subject.
    Returns total + per-type breakdown.
    """

    qs = (
        Resource.objects.filter(
            course__grade_subject__subject=subject,
            course__is_active=True,
            status="published",
        )
        .values("resource_type")
        .annotate(count=Count("id"))
    )

    counts = {row["resource_type"]: row["count"] for row in qs}

    return {
        "lessons_count": counts.get(ResourceType.LESSON, 0),
        "exercises_count": counts.get(ResourceType.EXERCISE, 0),
        "homeworks_count": counts.get(ResourceType.HOMEWORK, 0),
        "summaries_count": counts.get(ResourceType.SUMMARY, 0),
        "notes_count": counts.get(ResourceType.NOTES, 0),
        "series_count": counts.get(ResourceType.SERIES, 0),
        "course_resources_count": sum(counts.values()),
    }


def get_progress_counts_for_student(student, grade_subject_ids):
    """Completed courses per grade_subject for a given student."""

    course_ct = ContentType.objects.get_for_model(Course)

    completed_course_ids = ContentProgress.objects.filter(
        student=student,
        content_type=course_ct,
        is_completed=True,
    ).values_list("object_id", flat=True)

    # Cast object_id strings to the same type as Course.pk
    return dict(
        Course.objects.filter(
            pk__in=completed_course_ids,
            grade_subject_id__in=grade_subject_ids,
            is_active=True,
        )
        .values("grade_subject_id")
        .annotate(count=Count("id"))
        .values_list("grade_subject_id", "count")
    )


def get_student_progress_for_subject(student, subject):
    """
    Returns (completed_courses, total_courses, progress_pct) for a student.
    """

    course_ct = ContentType.objects.get_for_model(Course)

    total = Course.objects.filter(
        grade_subject__subject=subject,
        is_active=True,
    ).count()

    if not total:
        return {"completed_courses": 0, "total_courses": 0, "progress": 0}

    completed = ContentProgress.objects.filter(
        student=student,
        content_type=course_ct,
        is_completed=True,
        object_id__in=Course.objects.filter(
            grade_subject__subject=subject,
            is_active=True,
        ).values("id"),
    ).count()

    return {
        "completed_courses": completed,
        "total_courses": total,
        "progress": round(completed / total * 100, 1),
    }


def get_level_stats(level):
    return {
        "grades": Grade.objects.filter(level=level).count(),
        "subjects": level.subjects.count(),
        "students": (
            CustomUser.objects.filter(
                role=UserRole.STUDENT,
                student_profile__grade__level=level,
            )
            .distinct()
            .count()
        ),
    }


# ── append to apps/curriculum/selectors.py ─────────────────────────────────

# Term ↔ Quarter mapping — single source of truth
QUARTER_TO_TERM = {
    "q1": "first",
    "q2": "second",
    "q3": "third",
}

TERM_TO_QUARTER = {v: k for k, v in QUARTER_TO_TERM.items()}


def resolve_term(quarter: str) -> str:
    """
    Converts 'q1' → 'first', raises ValueError on invalid input.
    """
    term = QUARTER_TO_TERM.get(quarter.lower())
    if not term:
        raise ValueError(
            f"Invalid quarter '{quarter}'. Must be one of {list(QUARTER_TO_TERM)}"
        )
    return term


def get_subject_courses_by_quarter(subject, quarter: str, user=None):
    """
    Returns all active courses for a subject in a given quarter.

    Covers both:
      - Standalone courses: course.grade_subject.subject = subject, course.term = term
      - Chapter-based courses: course.chapter.grade_subject.subject = subject,
                                course.chapter.term = term

    Annotates each course with:
      - exercises_count
      - resources_count
      - progress_obj (ContentProgress) if user is an authenticated student
    """

    term = resolve_term(quarter)

    qs = (
        Course.objects.filter(is_active=True)
        .filter(
            # standalone: direct grade_subject → subject
            Q(
                chapter__isnull=True,
                grade_subject__subject=subject,
                term=term,
            )
            |
            # chapter-based: via chapter → grade_subject → subject
            Q(
                chapter__isnull=False,
                chapter__grade_subject__subject=subject,
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


def get_subject_resources(subject, resource_type, filters=None, user=None):
    """
    Generic resource selector for any subject resource type.
    Supports filters: q, difficulty, term.
    Subject resources are NOT linked to a course — they belong to Subject directly.
    """
    qs = Resource.objects.filter(
        grade_subject__subject=subject,
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


def get_grade_subject_by_pk(pk):
    try:
        return (
            GradeSubject.objects.filter(is_active=True)
            .annotate(
                tests_count=Count(
                    "resources",
                    filter=Q(
                        resources__resource_type=ResourceType.TEST,
                        resources__status="published",
                    ),
                    distinct=True,
                ),
                exams_count=Count(
                    "resources",
                    filter=Q(
                        resources__resource_type=ResourceType.EXAM,
                        resources__status="published",
                    ),
                    distinct=True,
                ),
                past_papers_count=Count(
                    "resources",
                    filter=Q(
                        resources__resource_type=ResourceType.PAST_PAPER,
                        resources__status="published",
                    ),
                    distinct=True,
                ),
                mock_exams_count=Count(
                    "resources",
                    filter=Q(
                        resources__resource_type=ResourceType.MOCK_EXAM,
                        resources__status="published",
                    ),
                    distinct=True,
                ),
                textbooks_count=Count(
                    "resources",
                    filter=Q(
                        resources__resource_type=ResourceType.TEXTBOOK,
                        resources__status="published",
                    ),
                    distinct=True,
                ),
                foreign_books_count=Count(
                    "resources",
                    filter=Q(
                        resources__resource_type=ResourceType.FOREIGN_BOOK,
                        resources__status="published",
                    ),
                    distinct=True,
                ),
                study_guides_count=Count(
                    "resources",
                    filter=Q(
                        resources__resource_type=ResourceType.STUDY_GUIDE,
                        resources__status="published",
                    ),
                    distinct=True,
                ),
            )
            .get(pk=pk)
        )
    except GradeSubject.DoesNotExist:
        raise Http404("GradeSubject not found")
