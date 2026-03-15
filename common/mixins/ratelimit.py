# common/mixins/ratelimit.py

import logging

from django.http import HttpRequest
from django_ratelimit.decorators import ratelimit
from django_ratelimit.exceptions import Ratelimited

from config.errors import error_429

logger = logging.getLogger(__name__)


class RatelimitMixin:
    """
    Applies rate limiting to any CBV.

    Subclasses define:
        ratelimit_key    : str  — "ip", "user", "user_or_ip", "post:email"
        ratelimit_rate   : str  — "5/m", "100/h" etc.
        ratelimit_method : str  — "POST", "GET", "ALL"
        ratelimit_block  : bool — True raises Ratelimited, False just sets flag
    """

    ratelimit_key = "user_or_ip"
    ratelimit_rate = "60/m"
    ratelimit_method = "ALL"
    ratelimit_block = True

    def dispatch(self, request: HttpRequest, *args, **kwargs):
        # ── Build and apply the decorator at dispatch time ─────────────────────
        # The decorator must be applied here — not at class definition time —
        # because the rate/key/method values come from instance attributes
        # which are only known when the view is instantiated.
        decorator = ratelimit(
            key=self.ratelimit_key,
            rate=self.ratelimit_rate,
            method=self.ratelimit_method,
            block=self.ratelimit_block,
        )

        # Wrap the parent dispatch with the decorator and call it
        try:
            return decorator(super().dispatch)(request, *args, **kwargs)
        except Ratelimited:
            logger.warning(
                "ratelimit.exceeded",
                extra={
                    "view": self.__class__.__name__,
                    "path": request.path,
                    "rate": self.ratelimit_rate,
                    "key": self.ratelimit_key,
                    "user_id": (
                        str(request.user.pk) if request.user.is_authenticated else None
                    ),
                },
            )
            request.retry_after = 60
            return error_429(request)
