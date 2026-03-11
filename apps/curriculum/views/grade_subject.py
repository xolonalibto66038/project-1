from django.http import Http404
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, ListView

from apps.content.choices import DifficultyLevel, ResourceType, Term

from ..mixins import GradeSubjectQuarterMixin
from ..models import GradeSubject
from ..selectors import (
    get_grade_subject_by_pk,
    get_grade_subject_counts_by_quarter,
    get_grade_subject_resources,
)
from ..services import build_grade_subject_courses_page

SUBJECT_RESOURCE_TYPE_CONFIG = {
    "tests": {
        "resource_type": ResourceType.TEST,
        "tab": "tests",
        "title": _("Tests"),
        "icon": "fas fa-clipboard-check",
    },
    "exams": {
        "resource_type": ResourceType.EXAM,
        "tab": "exams",
        "title": _("Exams"),
        "icon": "fas fa-file-alt",
    },
    "past-papers": {
        "resource_type": ResourceType.PAST_PAPER,
        "tab": "past-papers",
        "title": _("Past Papers"),
        "icon": "fas fa-file-signature",
    },
    "mock-exams": {
        "resource_type": ResourceType.MOCK_EXAM,
        "tab": "mock-exams",
        "title": _("Mock Exams"),
        "icon": "fas fa-stopwatch",
    },
    "textbooks": {
        "resource_type": ResourceType.TEXTBOOK,
        "tab": "textbooks",
        "title": _("Textbooks"),
        "icon": "fas fa-book-open",
    },
    "foreign-books": {
        "resource_type": ResourceType.FOREIGN_BOOK,
        "tab": "foreign-books",
        "title": _("Foreign Books"),
        "icon": "fas fa-book",
    },
    "study-guides": {
        "resource_type": ResourceType.STUDY_GUIDE,
        "tab": "study-guides",
        "title": _("Study Guides"),
        "icon": "fas fa-book-reader",
    },
}


class GradeSubjectDetailView(DetailView):
    model = GradeSubject
    template_name = "apps/curriculum/grade_subjects/detail.html"
    context_object_name = "grade_subject"

    def get_object(self, queryset=None):
        if not hasattr(self, "_grade_subject"):
            # No term filter here — we want the unfiltered object for breadcrumbs
            self._grade_subject = get_grade_subject_by_pk(pk=self.kwargs["pk"])
        return self._grade_subject

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        gs = self.get_object()

        grade = gs.grade
        level = grade.level
        subject = gs.subject

        # One DB hit per term (3 total) — returns counts for all quarters
        counts_by_quarter = get_grade_subject_counts_by_quarter(pk=self.kwargs["pk"])

        context.update(
            {
                "grade": grade,
                "level": level,
                "subject": subject,
                "specialty": gs.specialty,
                "quarters": Term.choices,
                "current_quarter": Term.FIRST,
                "counts_by_quarter": counts_by_quarter,
                "is_student": (
                    self.request.user.is_authenticated
                    and getattr(self.request.user, "is_student", False)
                ),
                # Subject resource tab config — slugs + icons only, counts come from counts_by_quarter
                "subject_resource_tabs": [
                    ("tests", "Tests", "fas fa-clipboard-check"),
                    ("exams", "Exams", "fas fa-file-alt"),
                    ("past-papers", "Past Papers", "fas fa-file-signature"),
                    ("mock-exams", "Mock Exams", "fas fa-stopwatch"),
                    ("textbooks", "Textbooks", "fas fa-book-open"),
                    ("foreign-books", "Foreign Books", "fas fa-book"),
                    ("study-guides", "Study Guides", "fas fa-book-reader"),
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


class GradeSubjectResourceListView(GradeSubjectQuarterMixin, ListView):
    """
    Generic view for all subject resource types (tests, exams, past papers, etc.)
    Driven by `resource_slug` URL kwarg — matches keys in SUBJECT_RESOURCE_TYPE_CONFIG.

    URL example:
        path('subjects/<uuid:pk>/resources/<str:resource_slug>/',
             SubjectResourceListView.as_view(),
             name='subject-resources'),
    """

    template_name = "apps/curriculum/subjects/resource_list.html"
    context_object_name = "resources"
    paginate_by = 9

    def _get_config(self):
        slug = self.kwargs.get("resource_slug")
        config = SUBJECT_RESOURCE_TYPE_CONFIG.get(slug)
        if not config:
            raise Http404(f"Unknown subject resource type: {slug}")
        return config

    def get_queryset(self):
        config = self._get_config()
        return get_grade_subject_resources(
            grade_subject=self.grade_subject,
            resource_type=config["resource_type"],
            filters=self.request.GET,
            user=self.request.user,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        config = self._get_config()

        qp = self.request.GET.copy()
        qp.pop("page", None)

        context.update(
            {
                "active_tab": config["tab"],
                "resource_type_title": config["title"],
                "resource_type_icon": config["icon"],
                "resource_type": config["resource_type"],
                "difficulty_choices": DifficultyLevel.choices,
                "term_choices": Term.choices,
                "querystring": qp.urlencode(),
                "filter_q": self.request.GET.get("q", ""),
                "filter_difficulty": self.request.GET.get("difficulty", ""),
                "filter_term": self.request.GET.get("term", ""),
            }
        )

        return context
