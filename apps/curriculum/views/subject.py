from django.http import Http404
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, ListView

from apps.content.choices import DifficultyLevel, ResourceType, Term
from apps.content.selectors import get_subject_resource_counts_by_quarter

from ..mixins import SubjectMixin, SubjectQuarterMixin
from ..models import Subject
from ..selectors import get_subject_resources
from ..services import get_subject_detail
from ..services.subject import build_courses_page

# Term → quarter slug mapping (Term choices: first/second/third)
_TERM_TO_QUARTER = {
    "first": "q1",
    "second": "q2",
    "third": "q3",
}

# Quarter slug → Term value
_QUARTER_TO_TERM = {v: k for k, v in _TERM_TO_QUARTER.items()}

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


def _current_quarter_from_request(request):
    """
    Reads ?quarter=q1/q2/q3 from GET params.
    Falls back to q1.
    """
    q = request.GET.get("quarter", "q1")
    return q if q in ("q1", "q2", "q3") else "q1"


class SubjectDetailView(SubjectMixin, DetailView):
    model = Subject
    template_name = "apps/curriculum/subjects/detail.html"
    context_object_name = "subject"
    pk_url_kwarg = "pk"

    def get_queryset(self):
        return Subject.objects.select_related("level")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        subject = self.object
        current_quarter = _current_quarter_from_request(self.request)

        stats = get_subject_detail(
            subject=subject,
            user=self.request.user,
        )

        context.update(stats)
        context.update(
            {
                "quarters": [
                    ("q1", _("1st Term")),
                    ("q2", _("2nd Term")),
                    ("q3", _("3rd Term")),
                ],
                "current_quarter": current_quarter,
                "level": subject.level,
                "counts_by_quarter": get_subject_resource_counts_by_quarter(subject),
            }
        )

        return context


class SubjectResourceListView(SubjectMixin, ListView):
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
        return get_subject_resources(
            subject=self.subject,
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


class SubjectCoursesByQuarterView(SubjectQuarterMixin, ListView):
    template_name = "apps/curriculum/subjects/courses_by_quarter.html"
    context_object_name = "courses"
    paginate_by = 20

    # ListView.get_queryset is bypassed — we build the list ourselves
    # and hand it back as a plain Python list for the paginator.
    def get_queryset(self):
        return build_courses_page(
            subject=self.subject,
            quarter=self.quarter,
            user=self.request.user,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # subject/quarter/level already injected by SubjectQuarterMixin
        context["quarter_display"] = {
            "q1": "1st Term",
            "q2": "2nd Term",
            "q3": "3rd Term",
        }.get(self.quarter, self.quarter.upper())

        context["is_student"] = self.request.user.is_authenticated and getattr(
            self.request.user, "is_student", False
        )

        # preserve GET params for pagination links (strip 'page')
        qp = self.request.GET.copy()
        qp.pop("page", None)
        context["querystring"] = qp.urlencode()

        return context
