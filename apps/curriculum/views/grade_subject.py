from django.views.generic import DetailView, ListView

from apps.content.choices import Term

from ..mixins import GradeSubjectQuarterMixin
from ..models import GradeSubject
from ..selectors import get_grade_subject_by_pk
from ..services import build_grade_subject_courses_page


class GradeSubjectDetailView(DetailView):
    model = GradeSubject
    template_name = "apps/curriculum/grade_subjects/detail.html"
    context_object_name = "grade_subject"

    def get_term(self):
        term = self.kwargs.get("term")
        if term and term in Term.values:
            return term
        return None

    def get_object(self, queryset=None):
        if not hasattr(self, "_grade_subject"):
            self._grade_subject = get_grade_subject_by_pk(
                pk=self.kwargs["pk"],
                term=self.get_term(),
            )
        return self._grade_subject

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        gs = self.get_object()
        term = self.get_term()

        grade = gs.grade
        level = grade.level
        subject = gs.subject

        context.update(
            {
                "grade": grade,
                "level": level,
                "subject": subject,
                "specialty": gs.specialty,
                "term": term,
                "term_display": dict(Term.choices).get(term, "") if term else "",
                "quarters": Term.choices,
                "current_quarter": term or Term.FIRST,
                "is_student": (
                    self.request.user.is_authenticated
                    and getattr(self.request.user, "is_student", False)
                ),
                # ── Counts passed to template ──
                "courses_count": gs.courses_count,
                "quizzes_count": 0,  # assessment app — wire up when ready
                # Course resource tabs
                "course_resource_tabs": [
                    (
                        "lessons",
                        "Lessons",
                        "fas fa-chalkboard-teacher",
                        gs.lessons_count,
                    ),
                    ("summaries", "Summaries", "fas fa-align-left", gs.summaries_count),
                    (
                        "homeworks",
                        "Homeworks",
                        "fas fa-pencil-ruler",
                        gs.homeworks_count,
                    ),
                    ("exercises", "Exercises", "fas fa-pencil-alt", gs.exercises_count),
                    ("notes", "Notes", "fas fa-sticky-note", gs.notes_count),
                    ("series", "Series", "fas fa-layer-group", gs.series_count),
                ],
                # Subject resource tabs
                "subject_resource_tabs": [
                    ("tests", "Tests", "fas fa-clipboard-check", gs.tests_count),
                    ("exams", "Exams", "fas fa-file-alt", gs.exams_count),
                    (
                        "past-papers",
                        "Past Papers",
                        "fas fa-file-signature",
                        gs.past_papers_count,
                    ),
                    (
                        "mock-exams",
                        "Mock Exams",
                        "fas fa-stopwatch",
                        gs.mock_exams_count,
                    ),
                    ("textbooks", "Textbooks", "fas fa-book-open", gs.textbooks_count),
                    (
                        "foreign-books",
                        "Foreign Books",
                        "fas fa-book",
                        gs.foreign_books_count,
                    ),
                    (
                        "study-guides",
                        "Study Guides",
                        "fas fa-book-reader",
                        gs.study_guides_count,
                    ),
                ],
            }
        )

        return context


class GradeSubjectCoursesByQuarterView(GradeSubjectQuarterMixin, ListView):
    template_name = "apps/curriculum/subjects/courses_by_quarter.html"
    context_object_name = "courses"
    paginate_by = 20

    # ListView.get_queryset is bypassed — we build the list ourselves
    # and hand it back as a plain Python list for the paginator.
    def get_queryset(self):
        return build_grade_subject_courses_page(
            grade_subject=self.grade_subject,
            quarter=self.kwargs.get("quarter"),  # ← pass raw URL kwarg directly
            user=self.request.user,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        term = self.get_term()
        context["quarter_display"] = dict(Term.choices).get(term, term or "")
        context["is_student"] = self.request.user.is_authenticated and getattr(
            self.request.user, "is_student", False
        )
        qp = self.request.GET.copy()
        qp.pop("page", None)
        context["querystring"] = qp.urlencode()

        return context
