# apps/billing/mixins.py

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect

from .choices import OfferTier
from .exceptions import SubscriptionRequired
from .helpers import _deny_access, _has_tier


class _TierRequiredMixin(LoginRequiredMixin):
    """
    Base mixin. Set `required_tier` on the subclass.
    """

    required_tier = OfferTier.STANDARD

    def dispatch(self, request, *args, **kwargs):
        # LoginRequiredMixin handles unauthenticated → login redirect
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        if _has_tier(request.user, self.required_tier):
            return super().dispatch(request, *args, **kwargs)

        # # Raise — middleware handles the redirect with full context
        # raise SubscriptionRequired(
        #     required_tier=self.required_tier,
        #     next_url=request.path,
        # )
        return _deny_access(request, self.required_tier)


class SubscriptionRequiredMixin(_TierRequiredMixin):
    """
    Requires *any* active paid subscription (Standard or above).

    Usage:
        class MyView(SubscriptionRequiredMixin, View): ...
    """

    # subscription_redirect_url = "billing:pricing"

    # def dispatch(self, request, *args, **kwargs):
    #     # Let LoginRequiredMixin handle unauthenticated users first
    #     response = super().dispatch(request, *args, **kwargs)

    #     if not request.user.is_authenticated:
    #         return response

    #     if _has_tier(request.user, OfferTier.STANDARD):
    #         return self.get_handler(request, *args, **kwargs)

    #     return redirect(self.subscription_redirect_url)

    # def get_handler(self, request, *args, **kwargs):
    #     """Call the real view handler after access is granted."""
    #     return super(LoginRequiredMixin, self).dispatch(request, *args, **kwargs)
    required_tier = OfferTier.STANDARD


class PremiumRequiredMixin(_TierRequiredMixin):
    """
    Requires a Premium subscription (e.g. online tutor access).

    Usage:
        class TutorView(PremiumRequiredMixin, View): ...
    """

    # subscription_redirect_url = "billing:pricing"

    # def dispatch(self, request, *args, **kwargs):
    #     response = super().dispatch(request, *args, **kwargs)

    #     if not request.user.is_authenticated:
    #         return response

    #     if _has_tier(request.user, OfferTier.PREMIUM):
    #         return self.get_handler(request, *args, **kwargs)

    #     return redirect(self.subscription_redirect_url)

    # def get_handler(self, request, *args, **kwargs):
    #     return super(LoginRequiredMixin, self).dispatch(request, *args, **kwargs)
    required_tier = OfferTier.PREMIUM
