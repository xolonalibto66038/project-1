from functools import wraps

from django.shortcuts import redirect

from .choices import OfferTier
from .exceptions import SubscriptionRequired
from .helpers import _deny_access, _has_tier


# def subscription_required(
#     view_func=None, *, tier=OfferTier.STANDARD, redirect_url="billing:pricing"
# ):
def subscription_required(view_func=None, *, tier=OfferTier.STANDARD):
    """
    Blocks access unless the user has an active subscription at or above `tier`.

    Default tier: STANDARD  →  paid content / resources.

    Usage:
        @subscription_required
        def my_view(request): ...

        @subscription_required(tier=OfferTier.PREMIUM)
        def tutor_view(request): ...

        @subscription_required(tier=OfferTier.PREMIUM, redirect_url="billing:upgrade")
        def tutor_view(request): ...
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("account_login")

            if _has_tier(request.user, tier):
                return fn(request, *args, **kwargs)

            # return redirect(redirect_url)

            # # Raise — middleware handles the redirect
            # raise SubscriptionRequired(
            #     required_tier=tier,
            #     next_url=request.path,
            # )
            # ← handle the redirect RIGHT HERE, no exception needed
            return _deny_access(request, tier)

        return wrapper

    # Support both @subscription_required and @subscription_required(tier=...)
    if view_func is not None:
        return decorator(view_func)

    return decorator


# Convenience alias — clearer intent at the call site
def premium_required(view_func=None, *, redirect_url="billing:pricing"):
    """
    Shorthand for @subscription_required(tier=OfferTier.PREMIUM).

    Usage:
        @premium_required
        def tutor_view(request): ...
    """
    # return subscription_required(
    #     view_func, tier=OfferTier.PREMIUM, redirect_url=redirect_url
    # )
    return subscription_required(view_func, tier=OfferTier.PREMIUM)
