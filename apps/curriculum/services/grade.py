import logging
from typing import Protocol, runtime_checkable

from django.http import HttpRequest
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from ..selectors.grade import build_enriched_grade_subjects
from .level import BreadcrumbBuilder  # shared base

logger = logging.getLogger(__name__)


class EnrichedSubjectBuilder:
    """
    Single responsibility: produce the enriched subject list for a grade page.

    Open for extension — override ``build`` to inject extra context,
    apply caching, or filter by feature flag without modifying the view.
    """

    def build(
        self,
        grade: object,
        user: object,
        specialty: object | None,
    ) -> list:
        return build_enriched_grade_subjects(
            grade=grade,
            user=user,
            specialty=specialty,
            student_grade=self._resolve_student_grade(user, grade),
        )

    @staticmethod
    def _resolve_student_grade(user: object, grade: object) -> object | None:
        """
        Returns the grade object only when the student belongs to it.
        Returns None for non-students, missing profiles, or grade mismatch.
        """
        if not (
            user is not None
            and user.is_authenticated
            and getattr(user, "is_student", False)
        ):
            return None

        profile = getattr(user, "student_profile", None)
        if profile is None:
            return None

        student_grade = getattr(profile, "grade", None)
        if student_grade is None:
            return None

        # The critical guard — only return if grades match
        return student_grade if student_grade.pk == grade.pk else None


@runtime_checkable
class SpecialtyResolverProtocol(Protocol):
    """
    Inversion boundary for specialty resolution.

    Each implementation represents one source in the priority chain.
    The view depends only on this protocol — never on concrete resolvers.
    """

    def resolve(
        self,
        user: object,
        grade: object,
        request: HttpRequest,
    ) -> object | None: ...


class ProfileSpecialtyResolver:
    """
    Strategy 1 — authenticated student's profile specialty.

    Returns the specialty only when it belongs to the current grade;
    silently returns None on any attribute error (missing profile, etc.).
    """

    def resolve(
        self,
        user: object,
        grade: object,
        request: HttpRequest,
    ) -> object | None:
        if not (user.is_authenticated and getattr(user, "is_student", False)):
            return None

        try:
            sp = user.student_profile.specialty
            if sp and sp.grade_id == grade.pk:
                return sp
        except Exception:
            logger.debug(
                "ProfileSpecialtyResolver: could not read specialty for user %s.",
                getattr(user, "pk", "?"),
            )
        return None


class QueryParamSpecialtyResolver:
    """
    Strategy 2 — ?specialty=<pk> query parameter.

    Validates the pk belongs to the requested grade to prevent
    cross-grade data leakage (IDOR guard).
    """

    PARAM_NAME = "specialty"

    def resolve(
        self,
        user: object,
        grade: object,
        request: HttpRequest,
    ) -> object | None:
        from ..models import Specialty  # local import avoids circular deps

        specialty_pk = request.GET.get(self.PARAM_NAME)
        if not specialty_pk:
            return None

        return (
            Specialty.objects.filter(pk=specialty_pk, grade=grade)
            .select_related("grade")
            .first()
        )


class ChainedSpecialtyResolver:
    """
    Composes an ordered list of resolvers and returns the first non-None result.

    Open for extension — pass a different resolver list to the constructor
    to reorder, add, or remove strategies without touching the view or any
    individual resolver.  Closed for modification.

    Default chain: profile → query param → None.
    """

    def __init__(
        self,
        resolvers: list[SpecialtyResolverProtocol] | None = None,
    ) -> None:
        self.resolvers: list[SpecialtyResolverProtocol] = resolvers or [
            ProfileSpecialtyResolver(),
            QueryParamSpecialtyResolver(),
        ]

    def resolve(
        self,
        user: object,
        grade: object,
        request: HttpRequest,
    ) -> object | None:
        for resolver in self.resolvers:
            result = resolver.resolve(user, grade, request)
            if result is not None:
                return result
        return None


class GradeDetailBreadcrumbBuilder(BreadcrumbBuilder):
    """
    Extends BreadcrumbBuilder (OCP) with the level crumb, then appends
    a dynamic terminal crumb showing grade name + optional specialty.

    The base chain (Home → Levels) is inherited unchanged.
    """

    CRUMB_DEFINITIONS: list[dict] = [
        {"label": _("Home"), "url_name": "pages:landing", "icon": "fas fa-home"},
        {"label": _("Levels"), "url_name": "curriculum:level:level-list"},
    ]

    def build_for_grade(
        self,
        grade: object,
        specialty: object | None,
    ) -> list[dict]:
        crumbs = self.build()

        crumbs.append(
            {
                "label": grade.level.get_name_display(),
                "url": reverse(
                    "curriculum:level:level-detail",
                    kwargs={"pk": grade.level.pk},
                ),
            }
        )

        terminal_label = grade.short_name
        if specialty:
            terminal_label = f"{terminal_label} — {specialty.short_name}"

        crumbs.append({"label": terminal_label, "url": None})
        return crumbs
