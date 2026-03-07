from ..selectors.subject import (
        get_courses_count_for_subject,
        get_course_resource_counts_for_subject,
        get_student_progress_for_subject,
        get_subject_resource_counts,
    )

def get_subject_detail(subject, user=None):
    """
    Assembles all stats needed for the subject detail page.
    Single entry point — view calls this, nothing else.

    Returns a flat dict ready for context.update().
    """

    is_student = (
        user is not None
        and user.is_authenticated
        and getattr(user, 'is_student', False)
    )

    courses_count        = get_courses_count_for_subject(subject)
    subject_res_counts   = get_subject_resource_counts(subject)
    course_res_counts    = get_course_resource_counts_for_subject(subject)

    resources_count = (
        subject_res_counts['subject_resources_count']
        + course_res_counts['course_resources_count']
    )

    progress_data = (
        get_student_progress_for_subject(user, subject)
        if is_student else
        {'completed_courses': 0, 'total_courses': 0, 'progress': 0}
    )

    return {
        'is_student':     is_student,
        'courses_count':  courses_count,
        'resources_count': resources_count,
        **subject_res_counts,   # tests_count, exams_count, subject_resources_count …
        **course_res_counts,    # lessons_count, exercises_count, course_resources_count …
        **progress_data,        # completed_courses, total_courses, progress
    }


def build_courses_page(subject, quarter: str, user=None):
    """
    Returns annotated course list for SubjectCoursesByQuarterView.
    Thin wrapper — keeps the view free of selector imports.
    """
    from ..selectors.subject import get_subject_courses_by_quarter
    return get_subject_courses_by_quarter(
        subject=subject,
        quarter=quarter,
        user=user,
    )