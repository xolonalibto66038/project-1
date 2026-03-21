from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse
from django.utils import timezone
from django.views import View

from apps.progress.models import ContentProgress

from ..models import VideoResource


class ToggleVideoSeenView(LoginRequiredMixin, View):

    http_method_names = ["post"]

    def dispatch(self, request, *args, **kwargs):
        if (
            request.user.is_authenticated
            and getattr(request.user, "role", None) != "student"
        ):
            return JsonResponse(
                {"error": "Only students can mark videos as seen."}, status=403
            )
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, pk):
        video = VideoResource.objects.filter(pk=pk, is_active=True).first()
        if not video:
            return JsonResponse({"error": "Video not found."}, status=404)

        ct = ContentType.objects.get_for_model(VideoResource)

        progress, created = ContentProgress.objects.get_or_create(
            student=request.user,
            content_type=ct,
            object_id=video.pk,
            defaults={
                "is_completed": True,
                "completed_at": timezone.now(),
                "first_viewed_at": timezone.now(),
            },
        )

        if not created:
            if progress.is_completed:
                progress.mark_incomplete()
            else:
                progress.mark_completed()

        return JsonResponse(
            {
                "seen": progress.is_completed,
                "video_id": str(video.pk),
                "seen_at": (
                    progress.completed_at.isoformat() if progress.completed_at else None
                ),
            }
        )
