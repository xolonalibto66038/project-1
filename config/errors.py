import logging

from django.shortcuts import render

logger = logging.getLogger(__name__)


def error_400(request, exception=None):
    return render(request, "errors/400.html", status=400)


def error_403(request, exception=None):
    return render(request, "errors/403.html", status=403)


def error_404(request, exception):
    return render(request, "errors/404.html", status=404)


def error_429(request, exception=None):
    """
    Called from your rate limiting middleware or view decorator.
    Passes retry_after if the middleware sets it on the request.
    """
    retry_after = getattr(request, "retry_after", None)

    logger.warning(
        "error.rate_limit_exceeded",
        extra={
            "path": request.path,
            "user_id": str(request.user.pk) if request.user.is_authenticated else None,
            "retry_after": retry_after,
        },
    )

    response = render(
        request,
        "errors/429.html",
        context={"retry_after": retry_after},
        status=429,
    )
    if retry_after:
        # Standard header — tells the browser and any HTTP client when to retry
        response["Retry-After"] = str(retry_after)

    return response


def error_500(request):
    return render(request, "errors/500.html", status=500)


def error_503(request, exception=None):
    """
    Called from your maintenance mode middleware.
    Passes maintenance_end if the middleware sets it on the request.
    """
    maintenance_end = getattr(request, "maintenance_end", None)

    logger.warning(
        "error.service_unavailable",
        extra={
            "path": request.path,
            "maintenance_end": str(maintenance_end) if maintenance_end else None,
        },
    )

    response = render(
        request,
        "errors/503.html",
        context={"maintenance_end": maintenance_end},
        status=503,
    )
    if maintenance_end:
        response["Retry-After"] = str(maintenance_end)

    return response
