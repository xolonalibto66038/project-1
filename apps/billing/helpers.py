from django.shortcuts import redirect

from .choices import OfferTier


def _get_user_tier(user):
    """Return the user's current OfferTier or None."""
    subscription = getattr(user, "subscription", None)
    if subscription and subscription.is_active:
        return subscription.tier  # e.g. "standard" / "premium"
    return None


def _has_tier(user, required_tier):
    """
    True if the user's tier meets or exceeds the required tier.

    Tier hierarchy (lowest → highest):
        FREE < STANDARD < PREMIUM

    Staff / superusers always pass.
    """
    if user.is_staff or user.is_superuser:
        return True

    HIERARCHY = [OfferTier.FREE, OfferTier.STANDARD, OfferTier.PREMIUM]

    user_tier = _get_user_tier(user)
    if user_tier is None:
        return False

    try:
        return HIERARCHY.index(user_tier) >= HIERARCHY.index(required_tier)
    except ValueError:
        return False


def _deny_access(request, required_tier):
    """Build the contextual redirect directly — no exception, no middleware needed."""
    from urllib.parse import urlencode

    from django.urls import reverse

    params = urlencode(
        {
            "required_tier": required_tier,
            "next": request.path,
        }
    )

    subscription = getattr(request.user, "subscription", None)
    is_paying = (
        request.user.is_authenticated
        and subscription is not None
        and subscription.is_active
    )

    base_url = reverse("billing:upgrade" if is_paying else "billing:pricing")
    return redirect(f"{base_url}?{params}")
