from collections import defaultdict
from django.db.models import Count

from ..models import Level, Grade


def get_level_by_pk(pk):
    return Level.objects.get(pk=pk)


def get_grades_for_level(level):
    """
    Returns grades for a level annotated with subject and specialty counts.
    Grouped by order for the accordion UI.
    """
    grades_qs = (
        Grade.objects
        .filter(level=level)
        .annotate(
            subjects_count   = Count('grade_subjects__subject', distinct=True),
            specialties_count= Count('specialties', distinct=True),
        )
        .order_by('order', 'name')
        .select_related('level')
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
        {'order': order, 'grades': grade_list}
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

    subjects_count = (
        level.subjects.count()
    )

    grades_count = grades_qs.count()

    students_count = (
        CustomUser.objects
        .filter(
            role=UserRole.STUDENT,
            student_profile__grade__level=level,
        )
        .distinct()
        .count()
    )

    return {
        'grades'  : grades_count,
        'subjects': subjects_count,
        'students': students_count,
    }
