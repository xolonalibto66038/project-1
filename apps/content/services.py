from .selectors import get_or_create_course_progress


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
