# common/logging/filters.py

import logging

from ..middleware.request_id import get_current_request_id


class RequestIDFilter(logging.Filter):
    """
    Injects the current request_id into every log record.
    When no request is active (management commands, signals),
    falls back to '-' so the field is always present.
    """

    def filter(self, record):
        record.request_id = get_current_request_id() or "-"
        return True
