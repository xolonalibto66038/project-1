import logging

from ..models import Grade

logger = logging.getLogger(__name__)


class GradeLoggingMixin:
    """Logs access to grade views."""

    def dispatch(self, request, *args, **kwargs):
        logger.info(
            f"{self.__class__.__name__} accessed",
            extra={
                "user_id": request.user.id if request.user.is_authenticated else None,
                "grade_pk": str(kwargs.get("pk", "")),
                "path": request.path,
            },
        )
        return super().dispatch(request, *args, **kwargs)


class GradeQuerySetMixin:
    """
    Single responsibility: provide the canonical Grade queryset
    with its level pre-fetched.

    Reusable across any Grade-based view — no logic tied to the detail page.
    """

    def get_queryset(self):
        return Grade.objects.select_related("level").all()
