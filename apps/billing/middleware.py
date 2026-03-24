from urllib.parse import urlencode

from django.shortcuts import redirect
from django.urls import reverse

from .exceptions import SubscriptionRequired


class SubscriptionGateMiddleware:
    """
    Catches SubscriptionRequired exceptions raised anywhere in the
    request cycle and redirects to the correct page with full context.

    - Unauthenticated / Free users  →  /billing/pricing/
    - Already-paying users          →  /billing/upgrade/

    Both carry ?required_tier=...&next=... so the destination page
    can be contextual and return the user to where they were.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            return self.get_response(request)
        except SubscriptionRequired as exc:
            return self._handle(request, exc)

    def _handle(self, request, exc):
        params = urlencode(
            {
                "required_tier": exc.required_tier,
                "next": exc.next_url or request.path,
            }
        )

        # Already a paying subscriber? → focused upgrade page
        # Everyone else?               → full pricing / marketing page
        subscription = getattr(request.user, "subscription", None)
        is_paying = (
            request.user.is_authenticated
            and subscription is not None
            and subscription.is_active
        )

        base_url = reverse("billing:upgrade" if is_paying else "billing:pricing")
        return redirect(f"{base_url}?{params}")
