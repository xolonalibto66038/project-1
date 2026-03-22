import logging

from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView

from ..mixins.grade import GradeLoggingMixin, GradeQuerySetMixin
from ..models import Grade
from ..services.grade import (
    ChainedSpecialtyResolver,
    EnrichedSubjectBuilder,
    GradeDetailBreadcrumbBuilder,
    SpecialtyResolverProtocol,
)

logger = logging.getLogger(__name__)


class GradeDetailView(GradeQuerySetMixin, GradeLoggingMixin, DetailView):
    """
    Displays the detail page for a single curriculum grade.

    Specialty resolution follows a priority chain:
        1. Authenticated student's profile specialty (if grade matches)
        2. ?specialty=<pk> query parameter
        3. None (anonymous / teacher with no param)

    All services are injected via __init__ — the view is fully testable
    without a database or request cycle.

    Responsibilities delegated:
        - GradeQuerySetMixin          → canonical queryset with level prefetch
        - ChainedSpecialtyResolver    → specialty priority chain
        - EnrichedSubjectBuilder      → subject list with enrichment metadata
        - GradeDetailBreadcrumbBuilder → resolved breadcrumb trail
    """

    model = Grade
    template_name = "apps/curriculum/grades/detail.html"
    context_object_name = "grade"

    # ── Dependency injection ──────────────────────────────────────────────────

    def __init__(
        self,
        specialty_resolver: SpecialtyResolverProtocol | None = None,
        subject_builder: EnrichedSubjectBuilder | None = None,
        breadcrumb_builder: GradeDetailBreadcrumbBuilder | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.specialty_resolver = specialty_resolver or ChainedSpecialtyResolver()
        self.subject_builder = subject_builder or EnrichedSubjectBuilder()
        self.breadcrumb_builder = breadcrumb_builder or GradeDetailBreadcrumbBuilder()

    # ── Context ───────────────────────────────────────────────────────────────

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        grade = self.object
        user = self.request.user

        specialty = self.specialty_resolver.resolve(user, grade, self.request)
        enriched_subjects = self.subject_builder.build(grade, user, specialty)

        context["specialty"] = specialty
        context["enriched_subjects"] = enriched_subjects
        context["crumbs"] = self.breadcrumb_builder.build_for_grade(grade, specialty)
        context["page_title"] = _("%(grade)s%(specialty)s") % {
            "grade": grade.short_name,
            "specialty": f" — {specialty.short_name}" if specialty else "",
        }
        context["page_description"] = _(
            "Subjects and resources for this grade and specialty."
        )
        return context
