from collections import defaultdict

from django.db.models import Count, Prefetch

from ..models import Grade, Level, Specialty


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


def get_grade_groups_with_specialties(level):
    """
    Returns grades for a level grouped by order.
    Grades with specialties are expanded — one entry per specialty.
    Grades without specialties appear once with specialty=None.

    Returns:
        [
            {
                'order': 1,
                'grade': <Grade>,
                'entries': [
                    {'grade': <Grade>, 'specialty': None},        # no-specialty grade
                    # OR
                    {'grade': <Grade>, 'specialty': <Specialty>}, # one per specialty
                ]
            },
            ...
        ]
    """
    grades = (
        Grade.objects.filter(level=level)
        .prefetch_related(
            Prefetch(
                "specialties",
                queryset=Specialty.objects.order_by("name"),
            )
        )
        .select_related("level")
        .order_by("order", "name")
    )

    grouped = defaultdict(lambda: {"grade": None, "entries": []})

    for grade in grades:
        specialties = list(grade.specialties.all())

        group = grouped[grade.order]
        group["grade"] = grade  # representative grade for the group header

        if specialties:
            for specialty in specialties:
                group["entries"].append(
                    {
                        "grade": grade,
                        "specialty": specialty,
                        "label": f"{grade.short_name} – {specialty.short_name}",
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
            "single": len(data["entries"])
            == 1,  # hint for template (no accordion needed)
        }
        for order, data in sorted(grouped.items())
    ]
