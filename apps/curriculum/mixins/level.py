from ..selectors import get_active_levels


class LevelQuerySetMixin:
    """
    Provides the standard Level queryset to any ListView.
    Override get_queryset() in the view for custom filtering.
    """

    def get_queryset(self):
        qs = get_active_levels()
        return qs
