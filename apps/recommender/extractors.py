# recommendations/extractors.py

"""
Feature extractors for the recommendation engine.
One extractor per registerable model — auto-registered via @register.

Resource hierarchy (all valid configurations):
    resource → course → chapter → grade_subject → subject / grade → level
    resource → course (standalone) → grade_subject → subject / grade → level
    resource → grade_subject (test / exam) → subject / grade → level

Course hierarchy:
    course → chapter → grade_subject → subject / grade → level
    course (standalone) → grade_subject → subject / grade → level
"""

import logging

from .registry import register

logger = logging.getLogger(__name__)


# ── Shared traversal helpers ───────────────────────────────────────────────────


def _grade_subject_from_resource(resource):
    """
    Resolve the GradeSubject for a Resource regardless of its parent config.

    Three valid configurations:
      1. resource.course.chapter.grade_subject   (chapter-based course)
      2. resource.course.grade_subject           (standalone course)
      3. resource.grade_subject                  (direct — test / exam)
    """
    if resource.course_id:
        course = resource.course
        if course.chapter_id:
            return course.chapter.grade_subject
        return course.grade_subject
    return resource.grade_subject


def _grade_subject_from_course(course):
    """
    Resolve the GradeSubject for a Course regardless of its parent config.

      1. course.chapter.grade_subject   (chapter-based)
      2. course.grade_subject           (standalone)
    """
    if course.chapter_id:
        return course.chapter.grade_subject
    return course.grade_subject


def _unpack_grade_subject(grade_subject):
    """
    Returns (level, grade, subject, specialty_id) from a GradeSubject instance.
    Returns (None, None, None, None) if grade_subject is None.
    """
    if grade_subject is None:
        return None, None, None, None

    grade = grade_subject.grade
    subject = grade_subject.subject
    level = grade.level

    return level, grade, subject, grade_subject.specialty_id


# ── Resource extractor ─────────────────────────────────────────────────────────


@register("resource")
def extract_resource(instance) -> dict:
    """
    Extracts a flat feature dict from a Resource instance.

    Handles all valid parent configurations — see module docstring.
    Falls back to None values for hierarchy fields when the resource
    is malformed (missing both course and grade_subject), so the engine
    can still process it without crashing.
    """
    grade_subject = _grade_subject_from_resource(instance)
    level, grade, subject, specialty_id = _unpack_grade_subject(grade_subject)

    if grade_subject is None:
        logger.warning(
            "extract_resource: Resource pk=%s has no resolvable GradeSubject. "
            "Hierarchy fields will be None — this resource won't match anything.",
            instance.pk,
        )

    return {
        "level_id": level.pk if level else None,
        "grade_id": grade.pk if grade else None,
        "subject_id": subject.pk if subject else None,
        # specialty_id: NULL means "applies to all" — see engine specialty rule
        "specialty_id": specialty_id,
        # course_id is only set for course-attached resources (lesson/exercise/homework)
        # test and exam attach directly to grade_subject, so course_id stays None
        "course_id": instance.course_id or None,
        "item_type": instance.resource_type,
        "difficulty": instance.difficulty or None,
        # term is inherited from course (which inherits from chapter)
        # or set directly on subject-level resources — already a string like "T1"
        "term": instance.term or None,
    }


# ── Course extractor ───────────────────────────────────────────────────────────


@register("course")
def extract_course(instance) -> dict:
    """
    Extracts a flat feature dict from a Course instance.

    course_id is set to the course's own PK so that resources belonging
    to this course score high when compared against it.
    """
    grade_subject = _grade_subject_from_course(instance)
    level, grade, subject, specialty_id = _unpack_grade_subject(grade_subject)

    if grade_subject is None:
        logger.warning(
            "extract_course: Course pk=%s has no resolvable GradeSubject. "
            "Hierarchy fields will be None — this course won't match anything.",
            instance.pk,
        )

    return {
        "level_id": level.pk if level else None,
        "grade_id": grade.pk if grade else None,
        "subject_id": subject.pk if subject else None,
        "specialty_id": specialty_id,
        # A course IS its own course context
        "course_id": instance.pk,
        "item_type": "course",
        "difficulty": instance.difficulty or None,
        # effective_term handles chapter inheritance transparently
        "term": instance.effective_term or None,
    }
