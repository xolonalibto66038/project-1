from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from django.urls import reverse
from django.utils.translation import gettext_lazy as _


@dataclass(frozen=True)
class Crumb:
    """
    Immutable breadcrumb item.

    ``url`` is None for the current (active) page — templates use this
    to decide whether to render a link or plain text.
    ``icon`` is an optional FontAwesome class string.
    """

    label: str
    url: str | None = None
    icon: str | None = None

    @classmethod
    def active(cls, label: str, icon: str | None = None) -> "Crumb":
        """Convenience constructor for the terminal (non-linked) crumb."""
        return cls(label=label, url=None, icon=icon)

    @classmethod
    def link(
        cls, label: str, url_name: str, icon: str | None = None, **kwargs
    ) -> "Crumb":
        """
        Convenience constructor that resolves a named URL immediately.
        kwargs are forwarded to ``reverse()`` as ``kwargs=``.
        """
        return cls(label=label, url=reverse(url_name, kwargs=kwargs or None), icon=icon)


@runtime_checkable
class BreadcrumbBuilderProtocol(Protocol):
    """
    DIP boundary — views depend on this, not on concrete builders.
    Any object with a matching ``build`` signature satisfies it.
    """

    def build(self, **ctx) -> list[Crumb]: ...


class BreadcrumbBuilder:
    """
    Base breadcrumb builder.

    Subclass per app and override ``get_crumbs``.  The ``build`` method
    handles URL resolution and is the stable public API.

    ``**ctx`` lets views pass runtime context (e.g. a model instance)
    so builders can produce dynamic crumbs without coupling to the request.

    Example — static crumbs:

        class CurriculumBreadcrumbs(BreadcrumbBuilder):
            def get_crumbs(self, **ctx) -> list[Crumb]:
                return [
                    Crumb.link(_("Home"), "pages:landing", icon="fas fa-home"),
                    Crumb.link(_("Curriculum"), "curriculum:index"),
                    Crumb.active(_("Levels")),
                ]

    Example — dynamic crumbs (object passed from view):

        class LevelDetailBreadcrumbs(BreadcrumbBuilder):
            def get_crumbs(self, **ctx) -> list[Crumb]:
                level = ctx["level"]
                return [
                    Crumb.link(_("Home"), "pages:landing", icon="fas fa-home"),
                    Crumb.link(_("Levels"), "curriculum:level-list"),
                    Crumb.active(level.get_name_display()),
                ]
    """

    def get_crumbs(self, **ctx) -> list[Crumb]:
        """
        Override in subclasses to return the crumb list for this view/app.
        ``ctx`` carries any runtime data passed from the view.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement get_crumbs()."
        )

    def build(self, **ctx) -> list[Crumb]:
        """
        Public API — called by BreadcrumbMixin.
        Validates output type in DEBUG so mistakes surface early.
        """
        crumbs = self.get_crumbs(**ctx)
        assert all(
            isinstance(c, Crumb) for c in crumbs
        ), f"{self.__class__.__name__}.get_crumbs() must return a list[Crumb]."
        return crumbs
