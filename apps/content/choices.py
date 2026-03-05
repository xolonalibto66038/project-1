from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _


class ResourceType(TextChoices):
    # Course-specific resource types
    LESSON   = 'lesson',   _('Lesson')
    EXERCISE = 'exercise', _('Exercise')
    HOMEWORK = 'homework', _('Homework')
    SUMMARY  = "summary",  _("Summary")
    NOTES    = "notes",    _("Notes")
    SERIES   = "series",   _("Series")

    # Subject-specific resource types
    TEST = "test", _("Test")
    EXAM = "exam", _("Exam")
    PAST_PAPER = "past_paper", _(
        "Past Paper"
    )
    MOCK_EXAM = "mock_exam", _("Mock Exam")
    TEXTBOOK = "textbook", _("Textbook")
    FOREIGN_BOOK = "foreign_book", _("Foreign Book")
    STUDY_GUIDE = "study_guide", _("Study Guide")

    @classmethod
    def get_course_choices(cls):
        """Get resource type choices available for courses."""
        return [
            (cls.LESSON, cls.LESSON.label),
            (cls.EXERCISE, cls.EXERCISE.label),
            (cls.SUMMARY, cls.SUMMARY.label),
            (cls.HOMEWORK, cls.HOMEWORK.label),
            (cls.NOTES, cls.NOTES.label),
            (cls.SERIES, cls.SERIES.label),
        ]

    @classmethod
    def get_subject_choices(cls):
        """Get resource type choices available for subjects."""
        return [
            (cls.TEST, cls.TEST.label),
            (cls.EXAM, cls.EXAM.label),
            (cls.PAST_PAPER, cls.PAST_PAPER.label),
            (cls.MOCK_EXAM, cls.MOCK_EXAM.label),
            (cls.TEXTBOOK, cls.TEXTBOOK.label),
            (cls.FOREIGN_BOOK, cls.FOREIGN_BOOK.label),
            (cls.STUDY_GUIDE, cls.STUDY_GUIDE.label),
        ]

    @classmethod
    def get_course_values(cls):
        """Get resource type values available for courses."""
        return [cls.LESSON, cls.EXERCISE, cls.HOMEWORK, cls.SUMMARY, cls.NOTES, cls.SERIES]

    @classmethod
    def get_subject_values(cls):
        """Get resource type values available for subjects."""
        return [
            cls.TEST,
            cls.EXAM,
            cls.PAST_PAPER,
            cls.MOCK_EXAM,
            cls.TEXTBOOK,
            cls.FOREIGN_BOOK,
            cls.STUDY_GUIDE,
        ]

    @classmethod
    def is_valid_for_course(cls, resource_type):
        """Check if resource type is valid for course."""
        return resource_type in cls.get_course_values()

    @classmethod
    def is_valid_for_subject(cls, resource_type):
        """Check if resource type is valid for subject."""
        return resource_type in cls.get_subject_values()


class DifficultyLevel(TextChoices):
    EASY   = 'easy',   _('Easy')
    MEDIUM = 'medium', _('Medium')
    HARD   = 'hard',   _('Hard')
    ADVANCED = "advanced", _("Advanced")

    @classmethod
    def color(self):
        return {
            "easy": "#28a745",  # Green
            "medium": "#ffc107",  # Yellow
            "hard": "#fd7e14",  # Orange
            "advanced": "#dc3545",  # Red
        }[self]


class ResourceStatus(TextChoices):
    DRAFT     = 'draft',     _('Draft')
    PUBLISHED = 'published', _('Published')
    ARCHIVED  = 'archived',  _('Archived')


class Term(TextChoices):
    FIRST  = 'first',  _('First Term')
    SECOND = 'second', _('Second Term')
    THIRD  = 'third',  _('Third Term')