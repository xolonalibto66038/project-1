from ..selectors import (
    get_course_counts_for_grade_subjects,
    get_course_resource_counts_for_grade_subjects,
    get_grade_subject_courses_by_quarter,
    get_grade_subjects_for_grade,
    get_progress_counts_for_student,
    get_resource_counts_for_grade_subjects,
)


def build_grade_subject_courses_page(
    grade_subject, quarter: str, user=None, difficulty=None, search=None
):
    """
    Returns annotated course list for SubjectCoursesByQuarterView.
    Thin wrapper — keeps the view free of selector imports.
    """

    return get_grade_subject_courses_by_quarter(
        grade_subject=grade_subject,
        quarter=quarter,
        user=user,
        difficulty=difficulty,
        search=search,
    )


def build_enriched_grade_subjects(grade, user=None, specialty=None):
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
    progress_counts = (
        get_progress_counts_for_student(user, grade_subject_ids) if is_student else {}
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
                "show_progress": is_student,
            }
        )

    return enriched
