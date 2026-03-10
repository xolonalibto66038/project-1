from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View

from .models import ContentProgress


class ToggleContentCompletedView(LoginRequiredMixin, View):
    """
    Generic view to toggle completion state for:
    - Course
    - Resource
    - Exercise
    """

    # 🔒 must match StudentContentProgress.ALLOWED_CONTENT_TYPES
    ALLOWED_MODELS = ("course", "resource", "exercise")

    def post(self, request, app_label, model, pk):
        # ---- Permissions ----
        if not getattr(request.user, "is_student", False):
            return redirect("home")

        model = model.lower()
        if model not in self.ALLOWED_MODELS:
            return redirect("home")

        # ---- Resolve content type safely ----
        content_type = get_object_or_404(
            ContentType,
            app_label=app_label,
            model=model,
        )

        # ---- Resolve target object (no direct import) ----
        model_class = content_type.model_class()
        obj = get_object_or_404(model_class, pk=pk)

        # ---- Progress ----
        progress, _ = ContentProgress.objects.get_or_create(
            student=request.user,
            content_type=content_type,
            object_id=obj.pk,
        )

        # ---- Toggle ----
        if progress.is_completed:
            progress.mark_incomplete()
        else:
            progress.mark_completed()

        # ---- Redirect back safely ----
        return redirect(
            request.META.get("HTTP_REFERER")
            or self.get_fallback_url(app_label, model, pk)
        )

    def get_fallback_url(self, app_label, model, pk):
        """
        Fallback URLs per content type
        """
        if model == "course":
            return reverse("content:course:course-detail", kwargs={"pk": pk})
        if model == "resource":
            return reverse("content:resource:resource-detail", kwargs={"pk": pk})
        if model == "exercise":
            return reverse("content:resource:exercise-detail", kwargs={"pk": pk})

        return reverse("home")
