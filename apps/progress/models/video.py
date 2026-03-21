from django.contrib.auth import get_user_model
from django.db import models

from apps.content.models import VideoResource
from common.models import TimeStampModel

User = get_user_model()


# models.py — add watched_seconds to ContentProgress or a separate model
class VideoWatchProgress(TimeStampModel):
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="watch_progress",
        limit_choices_to={"role": "student"},
    )
    video = models.ForeignKey(
        VideoResource, on_delete=models.CASCADE, related_name="watch_progress"
    )

    watched_seconds = models.PositiveIntegerField(default=0)
    duration_seconds = models.PositiveIntegerField(default=0)  # cached from player

    class Meta:
        unique_together = ("student", "video")
        indexes = [
            models.Index(fields=["student", "video"]),
        ]

    @property
    def percent(self):
        if not self.duration_seconds:
            return 0
        return round(self.watched_seconds / self.duration_seconds * 100)

    @property
    def is_seen(self):
        return self.percent >= 80

    def __str__(self):
        return f"{self.student} → {self.video.title} [{self.percent}%]"
