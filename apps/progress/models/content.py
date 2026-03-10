from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from common.models import TimeStampModel

User = get_user_model()


class ContentProgress(TimeStampModel):
    """
    Generic progress tracking for Course and Resource.
    """

    ALLOWED_MODELS = ("course", "resource")

    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="content_progress",
    )

    # ---- Generic target ----
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    content_object = GenericForeignKey("content_type", "object_id")

    # ---- Progress fields ----
    is_completed = models.BooleanField(default=False)
    first_viewed_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=_("First Viewed At"),
        help_text=_("Timestamp when the student first accessed this content."),
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Completed At"),
        help_text=_("Timestamp when the student completed this content."),
    )

    class Meta:
        unique_together = ("student", "content_type", "object_id")

        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(is_completed=False, completed_at__isnull=True)
                    | models.Q(is_completed=True, completed_at__isnull=False)
                ),
                name="completed_state_consistency",
            ),
        ]

        indexes = [
            models.Index(fields=["student", "content_type"]),
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["student", "is_completed"]),
            models.Index(fields=["completed_at"]),
        ]

    # -------------------------
    # VALIDATION
    # -------------------------
    def clean(self):
        if not self.content_type:
            return
        if self.content_type.model not in self.ALLOWED_MODELS:
            raise ValidationError(
                _(
                    "Progress tracking not allowed for '%(type)s'. Allowed: %(allowed)s."
                ),
                params={
                    "type": self.content_type.model,
                    "allowed": ", ".join(self.ALLOWED_MODELS),
                },
            )
        # ✅ consistent with CheckConstraint
        if self.is_completed and not self.completed_at:
            raise ValidationError(
                _("completed_at must be set when is_completed is True.")
            )
        if not self.is_completed and self.completed_at:
            raise ValidationError(
                _("completed_at must be empty when is_completed is False.")
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    # -------------------------
    # DOMAIN METHODS
    # -------------------------
    def mark_completed(self):
        """
        Safe, idempotent, race-condition resistant.
        """
        if self.is_completed:
            return False

        updated = (
            type(self)
            .objects.filter(pk=self.pk, is_completed=False)
            .update(
                is_completed=True,
                completed_at=timezone.now(),
                updated_at=timezone.now(),
            )
        )

        if updated:
            self.refresh_from_db()

        return bool(updated)

    def mark_incomplete(self):
        if not self.is_completed:
            return False

        updated = (
            type(self)
            .objects.filter(pk=self.pk, is_completed=True)
            .update(
                is_completed=False,
                completed_at=None,
                updated_at=timezone.now(),
            )
        )

        if updated:
            self.refresh_from_db()

        return bool(updated)
