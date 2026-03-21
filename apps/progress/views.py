from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View

from apps.content.models import VideoResource

from .models import ContentProgress, VideoWatchProgress


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


class SaveVideoProgressView(LoginRequiredMixin, View):
    http_method_names = ["post"]

    def dispatch(self, request, *args, **kwargs):
        if (
            request.user.is_authenticated
            and getattr(request.user, "role", None) != "student"
        ):
            return JsonResponse(
                {"error": "Only students can save progress."}, status=403
            )
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, pk):
        import json

        video = VideoResource.objects.filter(pk=pk, is_active=True).first()
        if not video:
            return JsonResponse({"error": "Video not found."}, status=404)

        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON."}, status=400)

        watched_seconds = int(body.get("watched_seconds", 0))
        duration_seconds = int(body.get("duration_seconds", 0))

        obj, _ = VideoWatchProgress.objects.update_or_create(
            student=request.user,
            video=video,
            defaults={
                "watched_seconds": watched_seconds,
                "duration_seconds": duration_seconds,
            },
        )

        # Auto-mark ContentProgress as completed if >= 80%
        if obj.is_seen:
            from django.contrib.contenttypes.models import ContentType
            from django.utils import timezone

            from apps.progress.models import ContentProgress

            ct = ContentType.objects.get_for_model(VideoResource)
            cp, created = ContentProgress.objects.update_or_create(
                student=request.user,
                content_type=ct,
                object_id=video.pk,
                defaults={
                    "is_completed": True,
                    "completed_at": timezone.now(),
                    "first_viewed_at": timezone.now(),
                },
            )

            if not created and not cp.is_completed:
                cp.mark_completed()

        return JsonResponse(
            {
                "watched_seconds": obj.watched_seconds,
                "duration_seconds": obj.duration_seconds,
                "percent": obj.percent,
                "is_seen": obj.is_seen,
            }
        )
