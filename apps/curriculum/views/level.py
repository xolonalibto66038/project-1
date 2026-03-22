import logging

from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, ListView

from ..mixins import LevelQuerySetMixin
from ..models import Level
from ..services.level import (
    BreadcrumbBuilder,
    GradeGroupAssembler,
    LevelDetailBreadcrumbBuilder,
    LevelEnricher,
    LevelListMessageService,
    LevelStatsProvider,
    StudentGradeResolver,
    StudentGradeResolverProtocol,
    StudentLevelResolver,
    StudentLevelResolverProtocol,
)

logger = logging.getLogger(__name__)


class LevelListView(LevelQuerySetMixin, ListView):
    """
    Displays all curriculum levels with enriched presentation metadata.

    Levels are not paginated — the domain has a fixed small set (4 total).
    Inject custom services via constructor kwargs for testing or extension.

    Responsibilities delegated:
        - StudentLevelResolver  → who is this student and what level are they on?
        - LevelEnricher         → how does a level look in the template?
        - BreadcrumbBuilder     → what does the breadcrumb trail look like?
        - LevelListMessageService → what flash messages should fire?
    """

    template_name = "apps/curriculum/levels/list.html"
    context_object_name = "levels"

    # ── Dependency injection ──────────────────────────────────────────────────

    def __init__(
        self,
        resolver: StudentLevelResolverProtocol | None = None,
        enricher: LevelEnricher | None = None,
        breadcrumb_builder: BreadcrumbBuilder | None = None,
        message_service: LevelListMessageService | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.resolver = resolver or StudentLevelResolver()
        self.enricher = enricher or LevelEnricher()
        self.breadcrumb_builder = breadcrumb_builder or BreadcrumbBuilder()
        self.message_service = message_service or LevelListMessageService()

    # ── Queryset ──────────────────────────────────────────────────────────────

    def get_queryset(self):
        qs = super().get_queryset()
        if not qs.exists():
            logger.warning("LevelListView: queryset returned no Level objects.")
        return qs

    # ── Context ───────────────────────────────────────────────────────────────

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)

        student_level = self.resolver.resolve(self.request.user)
        enriched_levels = self.enricher.enrich_all(context["levels"], student_level)

        self.message_service.dispatch(self.request, enriched_levels, student_level)

        context["enriched_levels"] = enriched_levels
        context["crumbs"] = self.breadcrumb_builder.build()
        context["page_title"] = _("Curriculum Levels")
        context["page_description"] = _(
            "Browse all available curriculum levels and find the one that matches your studies."
        )
        return context


class LevelDetailView(DetailView):
    """
    Displays the detail page for a single curriculum level.

    Responsibilities delegated:
        - StudentGradeResolver       → which grade does this student belong to?
        - GradeGroupAssembler        → grade groups + specialties for this level
        - LevelStatsProvider         → aggregated level statistics
        - LevelDetailBreadcrumbBuilder → resolved breadcrumb trail

    All four services are injected via __init__, making the view fully
    testable without touching the database or request cycle.
    """

    model = Level
    template_name = "apps/curriculum/levels/detail.html"
    context_object_name = "level"

    # ── Dependency injection ──────────────────────────────────────────────────

    def __init__(
        self,
        grade_resolver: StudentGradeResolverProtocol | None = None,
        group_assembler: GradeGroupAssembler | None = None,
        stats_provider: LevelStatsProvider | None = None,
        breadcrumb_builder: LevelDetailBreadcrumbBuilder | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.grade_resolver = grade_resolver or StudentGradeResolver()
        self.group_assembler = group_assembler or GradeGroupAssembler()
        self.stats_provider = stats_provider or LevelStatsProvider()
        self.breadcrumb_builder = breadcrumb_builder or LevelDetailBreadcrumbBuilder()

    # ── Context ───────────────────────────────────────────────────────────────

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        level = self.object

        student_grade = self.grade_resolver.resolve(self.request.user)
        grade_groups = self.group_assembler.fetch(level, student_grade)
        stats = self.stats_provider.fetch(level)

        self._dispatch_messages(grade_groups, stats)

        context["grade_groups"] = grade_groups
        context["stats"] = stats
        context["crumbs"] = self.breadcrumb_builder.build_for_level(level)
        context["page_title"] = level.get_name_display()
        context["page_description"] = _(
            "Explore grades, specialties, and statistics for this curriculum level."
        )
        return context

    # ── Private ───────────────────────────────────────────────────────────────

    def _dispatch_messages(
        self,
        grade_groups: list,
        stats: dict,
    ) -> None:
        if not grade_groups:
            messages.warning(
                self.request,
                _("No grade groups are configured for this level yet."),
            )
            logger.warning(
                "LevelDetailView: no grade groups for level pk=%s.",
                self.object.pk,
            )

        if not stats:
            messages.info(
                self.request,
                _("Statistics for this level are not yet available."),
            )
            logger.info(
                "LevelDetailView: empty stats for level pk=%s.",
                self.object.pk,
            )
