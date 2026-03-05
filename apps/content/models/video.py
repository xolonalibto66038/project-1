from django.db import models
from django.utils.translation import gettext_lazy as _
from taggit.managers import TaggableManager

from common.models import UUIDTaggedItem, TimeStampModel


class VideoResource(TimeStampModel):

    course = models.ForeignKey(
        "Course", on_delete=models.CASCADE, related_name="videos"
    )

    title = models.CharField(max_length=255)

    youtube_url = models.URLField(
        help_text="Full YouTube URL (example: https://www.youtube.com/watch?v=abc123)"
    )

    order = models.PositiveIntegerField(default=0)

    duration = models.CharField(
        max_length=20, blank=True, help_text="Optional (example: 10:35)"
    )

    is_active = models.BooleanField(default=True)

    tags = TaggableManager(
        through=UUIDTaggedItem,
        blank=True,
        help_text=_(
            "Tags for categorizing and discovering resources "
            "(e.g., 'python', 'beginner', 'tutorial', 'exam-prep')"
        ),
        verbose_name=_("Tags"),
    )

    # author = models.ForeignKey(
    #     settings.AUTH_USER_MODEL,
    #     on_delete=models.SET_NULL,
    #     null=True,
    #     related_name='resources',
    #     verbose_name=_('Author'),
    #     help_text=_('The teacher who created this resource.'),
    # )

    class Meta:
        ordering = ["order"]
        verbose_name = "Course Video"
        verbose_name_plural = "Course Videos"

    def __str__(self):
        return f"{self.course} - {self.title}"

    @property
    def youtube_id(self):
        if "watch?v=" in self.youtube_url:
            return self.youtube_url.split("watch?v=")[1].split("&")[0]
        if "youtu.be/" in self.youtube_url:
            return self.youtube_url.split("youtu.be/")[1].split("?")[0]
