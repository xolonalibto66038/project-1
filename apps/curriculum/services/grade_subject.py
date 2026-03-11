def build_grade_subject_courses_page(grade_subject, quarter: str, user=None):
    """
    Returns annotated course list for SubjectCoursesByQuarterView.
    Thin wrapper — keeps the view free of selector imports.
    """
    from ..selectors.grade_subject import get_grade_subject_courses_by_quarter

    return get_grade_subject_courses_by_quarter(
        grade_subject=grade_subject,
        quarter=quarter,
        user=user,
    )
