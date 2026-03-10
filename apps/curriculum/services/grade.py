from ..selectors import (
    get_course_counts_for_subjects,
    get_course_resource_counts_for_subjects,
    get_grade_subjects_for_grade,
    get_progress_counts_for_student,
    get_resource_counts_for_subjects,
)


def build_enriched_subjects(grade, user=None, specialty=None):
    """
    Returns enriched subjects for a grade.
    If specialty is provided → only subjects linked to that specialty via GradeSubject.
    If specialty is None → subjects where GradeSubject.specialty is null (no-specialty grades).
    """
    grade_subjects = list(get_grade_subjects_for_grade(grade, specialty=specialty))
    subjects = [gs.subject for gs in grade_subjects]
    subject_ids = [s.id for s in subjects]

    if not subjects:
        return []

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
    for subject in subjects:
        sid = subject.id
        courses_count = course_counts.get(sid, 0)
        subject_resources_count = subject_resource_counts.get(sid, 0)
        course_resources_count = course_resource_counts.get(sid, 0)
        completed_courses = progress_counts.get(sid, 0)

        enriched.append(
            {
                "subject": subject,
                "courses_count": courses_count,
                "subject_resources_count": subject_resources_count,
                "course_resources_count": course_resources_count,
                "resources_count": subject_resources_count + course_resources_count,
                "completed_courses": completed_courses,
                "total_courses": courses_count,
                "progress": (
                    round(completed_courses / courses_count * 100, 1)
                    if courses_count
                    else 0
                ),
                "show_progress": is_student,
            }
        )

    return enriched


# def build_enriched_subjects(grade, user=None):
#     """
#     Returns a list of Subject objects annotated with:
#       - courses_count
#       - subject_resources_count
#       - course_resources_count
#       - resources_count  (combined)
#       - completed_courses (if student)
#       - total_courses
#       - progress (%)

#     Single responsibility: assembles per-subject stats
#     from individual selector calls.
#     """
#     subjects    = list(get_subjects_for_grade(grade))
#     subject_ids = [s.id for s in subjects]

#     if not subjects:
#         return []

#     course_counts          = get_course_counts_for_subjects(subject_ids)
#     subject_resource_counts = get_resource_counts_for_subjects(subject_ids)
#     course_resource_counts  = get_course_resource_counts_for_subjects(subject_ids)

#     is_student     = (
#         user is not None
#         and user.is_authenticated
#         and getattr(user, 'is_student', False)
#     )
#     progress_counts = (
#         get_progress_counts_for_student(user, subject_ids)
#         if is_student else {}
#     )

#     enriched = []
#     for subject in subjects:
#         sid = subject.id

#         courses_count           = course_counts.get(sid, 0)
#         subject_resources_count = subject_resource_counts.get(sid, 0)
#         course_resources_count  = course_resource_counts.get(sid, 0)
#         completed_courses       = progress_counts.get(sid, 0)

#         progress = (
#             round(completed_courses / courses_count * 100, 1)
#             if courses_count else 0
#         )

#         enriched.append({
#             'subject':                  subject,
#             'courses_count':            courses_count,
#             'subject_resources_count':  subject_resources_count,
#             'course_resources_count':   course_resources_count,
#             'resources_count':          subject_resources_count + course_resources_count,
#             'completed_courses':        completed_courses,
#             'total_courses':            courses_count,
#             'progress':                 progress,
#             'show_progress':            is_student,
#         })

#     return enriched
