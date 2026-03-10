from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect
from django.views import View

from apps.feedback.models import Rating


class RateContentView(LoginRequiredMixin, View):
    """
    Generic rating view for polymorphic content (Exercise, Resource).

    URL params:
    - app_label: e.g. 'content'
    - model_name: 'exercise' | 'resource'
    - pk: UUID of the object
    """

    def post(self, request, app_label, model_name, pk):
        # ---- permissions ----
        if not request.user.is_student:
            return HttpResponseBadRequest("Only students can rate content.")

        # ---- validate rating value ----
        try:
            value = int(request.POST.get("value"))
        except (TypeError, ValueError):
            return HttpResponseBadRequest("Invalid rating value.")

        if value < 1 or value > 5:
            return HttpResponseBadRequest("Rating must be between 1 and 5.")

        # ---- validate content type ----
        if model_name not in Rating.ALLOWED_MODELS:
            return HttpResponseBadRequest("Rating not allowed for this content type.")

        content_type = get_object_or_404(
            ContentType,
            app_label=app_label,
            model=model_name,
        )

        model_class = content_type.model_class()
        target_object = get_object_or_404(model_class, pk=pk)

        # ---- create or update rating ----
        Rating.objects.update_or_create(
            student=request.user,
            content_type=content_type,
            object_id=target_object.pk,
            defaults={
                "value": value,
                "active": True,
            },
        )

        # ---- redirect back ----
        return redirect(request.META.get("HTTP_REFERER", "/"))
