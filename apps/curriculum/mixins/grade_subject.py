from apps.content.choices import Term

from ..selectors import get_grade_subject_by_pk


class GradeSubjectQuarterMixin:
    """
    Resolves GradeSubject from URL pk and injects grade_subject/grade/level/subject/term into context.
    Optionally filters resource counts by term if `term` kwarg is present in the URL.
    """

    def get_term(self):
        """Resolve term from URL kwarg — None means all terms."""
        term = self.kwargs.get("quarter")
        if term and term in Term.values:
            return term
        return None

    def get_grade_subject(self):
        if not hasattr(self, "_grade_subject"):
            self._grade_subject = get_grade_subject_by_pk(
                pk=self.kwargs["pk"],
                term=self.get_term(),
            )
        return self._grade_subject

    @property
    def grade_subject(self):
        return self.get_grade_subject()

    def get_object(self, queryset=None):
        return self.get_grade_subject()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        gs = self.grade_subject
        term = self.get_term()

        context["grade_subject"] = gs
        context["subject"] = gs.subject
        context["grade"] = gs.grade
        context["level"] = gs.grade.level
        context["specialty"] = gs.specialty
        context["term"] = term
        context["term_display"] = dict(Term.choices).get(term, "") if term else ""
        context["is_student"] = self.request.user.is_authenticated and getattr(
            self.request.user, "is_student", False
        )
        context["course_resource_tabs"] = [
            ("lessons", "Lessons", "fas fa-chalkboard-teacher", gs.lessons_count),
            ("summaries", "Summaries", "fas fa-align-left", gs.summaries_count),
            ("homeworks", "Homeworks", "fas fa-pencil-ruler", gs.homeworks_count),
            ("exercises", "Exercises", "fas fa-pencil-alt", gs.exercises_count),
            ("notes", "Notes", "fas fa-sticky-note", gs.notes_count),
            ("series", "Series", "fas fa-layer-group", gs.series_count),
        ]
        context["subject_resource_tabs"] = [
            ("tests", "Tests", "fas fa-clipboard-check", gs.tests_count),
            ("exams", "Exams", "fas fa-file-alt", gs.exams_count),
            (
                "past-papers",
                "Past Papers",
                "fas fa-file-signature",
                gs.past_papers_count,
            ),
            ("mock-exams", "Mock Exams", "fas fa-stopwatch", gs.mock_exams_count),
            ("textbooks", "Textbooks", "fas fa-book-open", gs.textbooks_count),
            ("foreign-books", "Foreign Books", "fas fa-book", gs.foreign_books_count),
            (
                "study-guides",
                "Study Guides",
                "fas fa-book-reader",
                gs.study_guides_count,
            ),
        ]

        return context
