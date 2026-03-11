from apps.content.choices import Term

from ..selectors import get_grade_subject_by_pk, get_subject_by_pk

VALID_QUARTERS = ("q1", "q2", "q3")


class SubjectMixin:
    """
    Resolves subject from URL pk and injects subject/grade/level into context.
    """

    def get_subject(self):
        if not hasattr(self, "_subject"):
            self._subject = get_grade_subject_by_pk(self.kwargs["pk"])
        return self._subject

    @property
    def subject(self):
        return self.get_subject()

    def get_object(self, queryset=None):
        return self.get_subject()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        subject = self.subject
        level = subject.level

        context["subject"] = subject
        context["level"] = level
        context["is_student"] = self.request.user.is_authenticated and getattr(
            self.request.user, "is_student", False
        )

        context["subject_resource_tabs"] = [
            ("tests", "Tests", "fas fa-clipboard-check", subject.tests_count),
            ("exams", "Exams", "fas fa-file-alt", subject.exams_count),
            (
                "past-papers",
                "Past Papers",
                "fas fa-file-signature",
                subject.past_papers_count,
            ),
            ("mock-exams", "Mock Exams", "fas fa-stopwatch", subject.mock_exams_count),
            ("textbooks", "Textbooks", "fas fa-book-open", subject.textbooks_count),
            (
                "foreign-books",
                "Foreign Books",
                "fas fa-book",
                subject.foreign_books_count,
            ),
            (
                "study-guides",
                "Study Guides",
                "fas fa-book-reader",
                subject.study_guides_count,
            ),
        ]

        return context


class SubjectQuarterMixin:
    """
    Resolves subject from URL pk and injects subject/level/term into context.
    Optionally filters resource counts by term if `term` kwarg is present in the URL.
    """

    def get_term(self):
        """Resolve term from URL kwarg — None means all terms."""
        term = self.kwargs.get("term")
        if term and term in Term.values:
            return term
        return None

    def get_subject(self):
        if not hasattr(self, "_subject"):
            self._subject = get_subject_by_pk(
                pk=self.kwargs["pk"],
                term=self.get_term(),
            )
        return self._subject

    @property
    def subject(self):
        return self.get_subject()

    def get_object(self, queryset=None):
        return self.get_subject()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        subject = self.subject
        term = self.get_term()

        context["subject"] = subject
        context["level"] = subject.level
        context["term"] = term
        context["term_display"] = dict(Term.choices).get(term, "") if term else ""
        context["is_student"] = self.request.user.is_authenticated and getattr(
            self.request.user, "is_student", False
        )
        context["subject_resource_tabs"] = [
            ("tests", "Tests", "fas fa-clipboard-check", subject.tests_count),
            ("exams", "Exams", "fas fa-file-alt", subject.exams_count),
            (
                "past-papers",
                "Past Papers",
                "fas fa-file-signature",
                subject.past_papers_count,
            ),
            ("mock-exams", "Mock Exams", "fas fa-stopwatch", subject.mock_exams_count),
            ("textbooks", "Textbooks", "fas fa-book-open", subject.textbooks_count),
            (
                "foreign-books",
                "Foreign Books",
                "fas fa-book",
                subject.foreign_books_count,
            ),
            (
                "study-guides",
                "Study Guides",
                "fas fa-book-reader",
                subject.study_guides_count,
            ),
        ]

        return context


# class SubjectQuarterMixin:
#     """
#     Resolves `subject` and `quarter` from URL kwargs.
#     Validates quarter. Raises Http404 on invalid input.
#     Injects both into context automatically.
#     """

#     def dispatch(self, request, *args, **kwargs):

#         self.subject = get_object_or_404(
#             Subject.objects.select_related('level').only(
#                 'id', 'name', 'short_name', 'icon', 'level__id', 'level__name',
#             ),
#             pk=kwargs['pk'],
#         )

#         quarter = kwargs.get('quarter', '').lower()
#         if quarter not in VALID_QUARTERS:
#             raise Http404(
#                 f"Invalid quarter '{quarter}'. Must be one of {VALID_QUARTERS}"
#             )
#         self.quarter = quarter

#         return super().dispatch(request, *args, **kwargs)

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['subject'] = self.subject
#         context['quarter'] = self.quarter
#         context['level']   = self.subject.level
#         return context
