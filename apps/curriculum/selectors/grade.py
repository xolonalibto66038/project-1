from collections import defaultdict

from django.db.models import Count, Prefetch

from apps.curriculum.selectors.subject import (
    get_course_counts_for_subjects,
    get_course_resource_counts_for_subjects,
    get_progress_counts_for_student,
    get_resource_counts_for_subjects,
)

from ..models import Grade, Level, Specialty
from ..selectors.grade_subject import (
    get_course_counts_for_grade_subjects,
    get_course_resource_counts_for_grade_subjects,
    get_grade_subjects_for_grade,
    get_resource_counts_for_grade_subjects,
)


def get_level_by_pk(pk):
    return Level.objects.get(pk=pk)


def get_grades_for_level(level):
    """
    Returns grades for a level annotated with subject and specialty counts.
    Grouped by order for the accordion UI.
    """
    grades_qs = (
        Grade.objects.filter(level=level)
        .annotate(
            subjects_count=Count("grade_subjects__subject", distinct=True),
            specialties_count=Count("specialties", distinct=True),
        )
        .order_by("order", "name")
        .select_related("level")
    )
    return grades_qs


def get_grade_groups(level):
    """
    Groups grades by order for the accordion display.
    Grades with the same order = same year with multiple specialties.

    Returns:
        [{'order': 1, 'grades': [grade, ...]}, ...]
    """
    grades = get_grades_for_level(level)

    grouped = defaultdict(list)
    for grade in grades:
        grouped[grade.order].append(grade)

    return [
        {"order": order, "grades": grade_list}
        for order, grade_list in sorted(grouped.items())
    ]


def get_level_stats(level):
    """
    Aggregated stats for a level detail page.
    All in one place — easy to extend later.
    """
    from apps.accounts.choices import UserRole
    from apps.accounts.models.custom_user import CustomUser

    grades_qs = Grade.objects.filter(level=level)

    subjects_count = level.subjects.count()

    grades_count = grades_qs.count()

    students_count = (
        CustomUser.objects.filter(
            role=UserRole.STUDENT,
            student_profile__grade__level=level,
        )
        .distinct()
        .count()
    )

    return {
        "grades": grades_count,
        "subjects": subjects_count,
        "students": students_count,
    }


def get_grade_groups_with_specialties(level, student_grade=None):
    grades = (
        Grade.objects.filter(level=level)
        .prefetch_related(
            Prefetch("specialties", queryset=Specialty.objects.order_by("name"))
        )
        .select_related("level")
        .order_by("order", "name")
    )

    grouped = defaultdict(lambda: {"grade": None, "entries": []})

    for grade in grades:
        specialties = list(grade.specialties.all())
        is_student_grade = student_grade is not None and str(grade.pk) == str(
            student_grade.pk
        )

        group = grouped[grade.order]
        group["grade"] = grade
        group["is_student_grade"] = is_student_grade  # ← for group header highlight

        if specialties:
            for specialty in specialties:
                group["entries"].append(
                    {
                        "grade": grade,
                        "specialty": specialty,
                        "label": f"{grade.short_name} – {specialty.short_name}",
                        "is_student_grade": is_student_grade,
                        "url_kwargs": {
                            "grade_pk": grade.pk,
                            "specialty_pk": specialty.pk,
                        },
                    }
                )
        else:
            group["entries"].append(
                {
                    "grade": grade,
                    "specialty": None,
                    "label": grade.name,
                    "is_student_grade": is_student_grade,
                    "url_kwargs": {
                        "grade_pk": grade.pk,
                        "specialty_pk": None,
                    },
                }
            )

    return [
        {
            "order": order,
            "grade": data["grade"],
            "entries": data["entries"],
            "single": len(data["entries"]) == 1,
            "is_student_grade": data.get("is_student_grade", False),
        }
        for order, data in sorted(grouped.items())
    ]


def build_enriched_subjects(grade, user=None, specialty=None):
    grade_subjects = list(get_grade_subjects_for_grade(grade, specialty=specialty))

    if not grade_subjects:
        return []

    subject_ids = [gs.subject_id for gs in grade_subjects]

    course_counts = get_course_counts_for_subjects(subject_ids)
    subject_resource_counts = get_resource_counts_for_subjects(subject_ids)
    course_resource_counts = get_course_resource_counts_for_subjects(subject_ids)

    is_student = (
        user is not None
        and user.is_authenticated
        and getattr(user, "is_student", False)
    )
    progress_counts = (
        get_progress_counts_for_student(user, subject_ids) if is_student else {}
    )

    enriched = []
    for gs in grade_subjects:  # ← iterate GradeSubjects, not subjects
        sid = gs.subject_id
        courses_count = course_counts.get(sid, 0)
        completed = progress_counts.get(sid, 0)

        enriched.append(
            {
                "grade_subject": gs,  # ← keep the GradeSubject
                "subject": gs.subject,  # ← still available for display
                "courses_count": courses_count,
                "subject_resources_count": subject_resource_counts.get(sid, 0),
                "course_resources_count": course_resource_counts.get(sid, 0),
                "resources_count": subject_resource_counts.get(sid, 0)
                + course_resource_counts.get(sid, 0),
                "completed_courses": completed,
                "total_courses": courses_count,
                "progress": (
                    round(completed / courses_count * 100, 1) if courses_count else 0
                ),
                "show_progress": is_student,
            }
        )

    return enriched


def build_enriched_grade_subjects(
    grade,
    user=None,
    specialty=None,
    student_grade=None,
):
    grade_subjects = list(get_grade_subjects_for_grade(grade, specialty=specialty))

    if not grade_subjects:
        return []

    grade_subject_ids = [gs.pk for gs in grade_subjects]  # ← use GradeSubject PKs

    course_counts = get_course_counts_for_grade_subjects(grade_subject_ids)
    subject_resource_counts = get_resource_counts_for_grade_subjects(grade_subject_ids)
    course_resource_counts = get_course_resource_counts_for_grade_subjects(
        grade_subject_ids
    )

    is_student = (
        user is not None
        and user.is_authenticated
        and getattr(user, "is_student", False)
    )

    show_progress = student_grade is not None
    progress_counts = (
        get_progress_counts_for_student(user, grade_subject_ids)
        if show_progress
        else {}
    )

    enriched = []
    for gs in grade_subjects:
        gid = gs.pk  # ← key by GradeSubject PK, not subject_id
        courses_count = course_counts.get(gid, 0)
        completed = progress_counts.get(gid, 0)

        enriched.append(
            {
                "grade_subject": gs,
                "subject": gs.subject,
                "courses_count": courses_count,
                "subject_resources_count": subject_resource_counts.get(gid, 0),
                "course_resources_count": course_resource_counts.get(gid, 0),
                "resources_count": subject_resource_counts.get(gid, 0)
                + course_resource_counts.get(gid, 0),
                "completed_courses": completed,
                "total_courses": courses_count,
                "progress": (
                    round(completed / courses_count * 100, 1) if courses_count else 0
                ),
                "show_progress": show_progress,
            }
        )

    return enriched
