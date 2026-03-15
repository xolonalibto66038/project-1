# common/middleware/allauth_ratelimit.py

import logging

from allauth.core.exceptions import RateLimited

from config.errors import error_429

logger = logging.getLogger(__name__)


class AllauthRateLimitMiddleware:
    """
    Catches RateLimited raised by allauth and returns your custom 429 page.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if not isinstance(exception, RateLimited):
            return None

        logger.warning(
            "allauth.rate_limited",
            extra={
                "path": request.path,
                "user_id": (
                    str(request.user.pk) if request.user.is_authenticated else None
                ),
            },
        )

        request.retry_after = 60
        return error_429(request)
