# common/middleware/request_id.py
import logging
import threading
import uuid

from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

# Thread-local storage so the request ID is accessible
# anywhere in the same request/response cycle

_local = threading.local()


def get_current_request_id() -> str | None:
    return getattr(_local, "request_id", None)


class RequestIDMiddleware(MiddlewareMixin):
    """
    Assigns a unique request_id to every incoming request.
    Stored on thread-local so any logger can include it via the filter below.
    Also adds it to the response header so frontend/API clients can correlate.
    """

    def process_request(self, request):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.request_id = request_id
        _local.request_id = request_id

    def process_response(self, request, response):
        request_id = getattr(request, "request_id", None)
        if request_id:
            response["X-Request-ID"] = request_id
        # Clean up thread-local after response
        _local.request_id = None
        return response
