from ..models import Level


def get_active_levels():
    """
    Returns all levels ordered by their display order.
    Single source of truth for level queries across the app.
    """
    return Level.objects.all().only("id", "name", "slug", "order").order_by("order")
