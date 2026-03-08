# apps/billing/decorators.py

from functools import wraps
from django.shortcuts import redirect


def subscription_required(view_func):
    """
    Blocks access unless the user has an active subscription.
    Redirects unauthenticated users to login.
    Redirects users without active subscription to pricing page.
    Staff and superusers always pass through.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        if not request.user.is_authenticated:
            return redirect('account_login')

        # Staff bypass
        if request.user.is_staff or request.user.is_superuser:
            return view_func(request, *args, **kwargs)

        # Check your own Subscription model
        try:
            if request.user.subscription.is_active:
                return view_func(request, *args, **kwargs)
        except Exception:
            pass

        return redirect('billing:pricing')

    return wrapper