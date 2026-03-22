import logging
from typing import Protocol, runtime_checkable

from django.contrib import messages
from django.http import HttpRequest
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from ..consts import LEVEL_CONFIG
from ..selectors.grade import get_grade_groups_with_specialties, get_level_stats

logger = logging.getLogger(__name__)


@runtime_checkable
class StudentLevelResolverProtocol(Protocol):
    """
    Dependency inversion boundary.
    Any resolver passed to LevelListView must satisfy this interface.
    """

    def resolve(self, user: object) -> object | None: ...


@runtime_checkable
class StudentGradeResolverProtocol(Protocol):
    """
    Inversion boundary for grade resolution.

    Distinct from StudentLevelResolverProtocol (list view) — the detail
    view needs a grade, not a level. Keeping them separate satisfies ISP:
    neither protocol carries methods the consumer doesn't use.
    """

    def resolve(self, user: object) -> object | None: ...


class StudentLevelResolver:
    """
    Single responsibility: derive the Level instance for a student user.

    Follows DIP — LevelListView depends on the Protocol above,
    not on this concrete class directly.
    """

    def resolve(self, user: object) -> object | None:
        if not (user.is_authenticated and getattr(user, "is_student", False)):
            return None

        profile = getattr(user, "student_profile", None)
        if profile is None:
            logger.debug("User %s has no student_profile.", user.pk)
            return None

        grade = getattr(profile, "grade", None)
        if grade is None:
            logger.debug("User %s profile has no grade.", user.pk)
            return None

        return getattr(grade, "level", None)


class LevelEnricher:
    """
    Single responsibility: merge a Level ORM instance with its
    static presentation config from LEVEL_CONFIG.

    Open for extension — override ``get_config`` in a subclass to swap
    the config source (e.g. database-driven, A/B tested) without touching
    the view.  Closed for modification — the enrichment contract is stable.
    """

    def get_config(self, level: object) -> dict:
        return LEVEL_CONFIG.get(level.name, {})

    def enrich(self, level: object, student_level: object | None) -> dict:
        config = self.get_config(level)
        return {
            "level": level,
            "color": config.get("color", "secondary"),
            "image": config.get("image", "dist/img/levels/default.png"),
            "title": config.get("title", level.get_name_display()),
            "description": config.get("description", _("No description available.")),
            "is_student_level": (
                student_level is not None and level.pk == student_level.pk
            ),
        }

    def enrich_all(
        self,
        levels: list,
        student_level: object | None,
    ) -> list[dict]:
        return [self.enrich(level, student_level) for level in levels]


class StudentGradeResolver:
    """
    Single responsibility: derive the Grade instance for a student user.

    Returns None for anonymous users, non-students, or students without
    a grade assigned, logging each case at DEBUG level.
    """

    def resolve(self, user: object) -> object | None:
        if not (user.is_authenticated and getattr(user, "is_student", False)):
            return None

        profile = getattr(user, "student_profile", None)
        if profile is None:
            logger.debug("User %s has no student_profile.", user.pk)
            return None

        grade = getattr(profile, "grade", None)
        if grade is None:
            logger.debug("User %s profile has no grade assigned.", user.pk)

        return grade


class LevelListMessageService:
    """
    Single responsibility: evaluate enriched level state and emit
    the correct Django flash messages.

    Keeps all message logic out of the view and out of the enricher.
    """

    def dispatch(
        self,
        request: HttpRequest,
        enriched_levels: list[dict],
        student_level: object | None,
    ) -> None:
        if not enriched_levels:
            self._warn_empty(request)
            return

        if student_level is not None:
            self._handle_student(request, enriched_levels, student_level)

    # ── Private ──────────────────────────────────────────────────────────────

    def _warn_empty(self, request: HttpRequest) -> None:
        messages.warning(
            request,
            _(
                "No curriculum levels are available at the moment. Please check back later."
            ),
        )
        logger.warning(
            "LevelListView rendered with empty levels for user %s.",
            request.user.pk if request.user.is_authenticated else "anonymous",
        )

    def _handle_student(
        self,
        request: HttpRequest,
        enriched_levels: list[dict],
        student_level: object,
    ) -> None:
        matched = next((e for e in enriched_levels if e["is_student_level"]), None)
        if matched:
            logger.info(
                _("Your current level is highlighted below."),
            )
        else:
            logger.warning(
                "Student level pk=%s not found in enriched levels for user %s.",
                student_level.pk,
                request.user.pk,
            )


class GradeGroupAssembler:
    """
    Single responsibility: produce the grade-group-with-specialties
    data structure for a given level and optional student grade.

    Open for extension — subclass and override ``fetch`` to swap the
    underlying query (e.g. cached, filtered by feature flag) without
    touching the view.
    """

    def fetch(self, level: object, student_grade: object | None) -> list:
        return get_grade_groups_with_specialties(
            level,
            student_grade=student_grade,
        )


class LevelStatsProvider:
    """
    Single responsibility: retrieve aggregated statistics for a level.

    Open for extension — override ``fetch`` to add caching, mocking in
    tests, or alternative stat sources without touching the view.
    """

    def fetch(self, level: object) -> dict:
        return get_level_stats(level)


class BreadcrumbBuilder:
    """
    Single responsibility: build a resolved breadcrumb list.

    ``reverse()`` is deferred to call time so this is safe at module
    import — no ``AppRegistryNotReady`` or ``NoReverseMatch`` at startup.
    """

    CRUMB_DEFINITIONS: list[dict] = [
        {"label": _("Home"), "url_name": "pages:landing", "icon": "fas fa-home"},
        {"label": _("Levels"), "url": None},
    ]

    def build(self, extra_crumbs: list[dict] | None = None) -> list[dict]:
        crumbs = []
        for crumb in self.CRUMB_DEFINITIONS:
            entry = dict(crumb)
            if url_name := entry.pop("url_name", None):
                entry["url"] = reverse(url_name)
            crumbs.append(entry)

        for crumb in extra_crumbs or []:
            entry = dict(crumb)
            if url_name := entry.pop("url_name", None):
                entry["url"] = reverse(url_name)
            crumbs.append(entry)

        return crumbs

    @staticmethod
    def _display_name(obj: object) -> str:
        """
        Resolve the best human-readable label for any curriculum model.

        Priority:
          1. get_name_display()  — present when ``name`` is a choices field (e.g. Level)
          2. name                — full label (e.g. Grade.name)
          3. short_name          — compact fallback (e.g. Grade.short_name)
          4. str(obj)            — last resort, always defined
        """
        if callable(getattr(obj, "get_name_display", None)):
            return obj.get_name_display()
        if hasattr(obj, "name") and obj.name:
            return obj.name
        if hasattr(obj, "short_name") and obj.short_name:
            return obj.short_name
        return str(obj)


class LevelDetailBreadcrumbBuilder(BreadcrumbBuilder):
    """
    Extends BreadcrumbBuilder (OCP) with the Levels list crumb,
    then appends the dynamic level name as the terminal crumb.

    Closed for modification of the base chain — open for the detail
    layer added here.
    """

    CRUMB_DEFINITIONS: list[dict] = [
        {"label": _("Home"), "url_name": "pages:landing", "icon": "fas fa-home"},
        {"label": _("Levels"), "url_name": "curriculum:level:level-list"},
    ]

    def build_for_level(self, level: object) -> list[dict]:
        crumbs = self.build()
        crumbs.append({"label": level.get_name_display(), "url": None})
        return crumbs
