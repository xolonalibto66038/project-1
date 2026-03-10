from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import TimeStampModel

from ..choices import InteractionType

User = get_user_model()


class Interaction(TimeStampModel):
    """Track user interactions with resources"""

    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="interactions",
        verbose_name=_("Student"),
        db_index=True,
    )

    # Generic Foreign Key fields for polymorphic relationships
    content_type = models.ForeignKey(
        ContentType,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        verbose_name=_("Content Type"),
        help_text=_("Type of object being rated"),
    )

    object_id = models.UUIDField(
        null=True,
        blank=True,
        verbose_name=_("Object ID"),
        help_text=_("ID of the object being rated"),
    )

    content_object = GenericForeignKey("content_type", "object_id")

    interaction_type = models.CharField(
        max_length=20,
        choices=InteractionType.choices,
        default=InteractionType.RATE,
    )

    class Meta:
        verbose_name = _("Interaction")
        verbose_name_plural = _("Interactions")
        db_table = "user_interactions"
        ordering = ["-created_at"]
        # unique_together = ["student", "content_type", "object_id", "interaction_type"]
        indexes = [
            models.Index(fields=["student", "interaction_type"]),
            models.Index(fields=["content_type", "object_id", "interaction_type"]),
        ]
