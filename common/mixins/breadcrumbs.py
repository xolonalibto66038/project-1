from __future__ import annotations

from ..services import BreadcrumbBuilder, BreadcrumbBuilderProtocol, Crumb


class BreadcrumbMixin:
    """
    Generic mixin that injects ``crumbs`` into any CBV's template context.

    Usage in a view:

        class LevelListView(BreadcrumbMixin, LevelQuerySetMixin, ListView):
            breadcrumb_class = LevelListBreadcrumbs

    For dynamic crumbs that need a model instance, override
    ``get_breadcrumb_context`` in the view:

        def get_breadcrumb_context(self) -> dict:
            return {"level": self.get_object()}

    The mixin validates that ``breadcrumb_class`` satisfies the protocol,
    so misconfigured views fail loudly at startup rather than silently
    in production.
    """

    breadcrumb_class: type[BreadcrumbBuilderProtocol] | None = None

    def get_breadcrumb_builder(self) -> BreadcrumbBuilderProtocol:
        """
        Instantiate the builder.  Override to inject a custom instance
        (e.g. a mock in tests, or a builder fetched from a registry).
        """
        if self.breadcrumb_class is None:
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} must define `breadcrumb_class` "
                f"or override `get_breadcrumb_builder()`."
            )
        builder = self.breadcrumb_class()
        if not isinstance(builder, BreadcrumbBuilderProtocol):
            raise ImproperlyConfigured(
                f"{self.breadcrumb_class.__name__} does not satisfy "
                f"BreadcrumbBuilderProtocol."
            )
        return builder

    def get_breadcrumb_context(self) -> dict:
        """
        Override in the view to pass runtime context to the builder.
        Useful for detail views that need a model instance in the trail.
        """
        return {}

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        builder = self.get_breadcrumb_builder()
        context["crumbs"] = builder.build(**self.get_breadcrumb_context())
        return context
