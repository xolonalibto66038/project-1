# apps/billing/mixins.py

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect


class SubscriptionRequiredMixin(LoginRequiredMixin):
    """
    CBV equivalent of @subscription_required.
    """

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)

        if not request.user.is_authenticated:
            return response  # LoginRequiredMixin already handles redirect

        if request.user.is_staff or request.user.is_superuser:
            return response

        try:
            if request.user.subscription.is_active:
                return response
        except Exception:
            pass

        return redirect("billing:pricing")
