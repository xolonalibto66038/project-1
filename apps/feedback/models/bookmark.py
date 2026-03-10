from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import TimeStampModel

User = get_user_model()


class Bookmark(TimeStampModel):
    """
    Generic bookmark allowing a student to save any curriculum object.

    Uses Django's ContentTypes framework so any model can be bookmarked
    without adding new FK columns for each new content type.

    Business Rules:
    - A student can bookmark the same object only once.
    - content_type + object_id must always both be set.
    - Only allowed model types can be bookmarked (enforced via clean()).

    Examples:
        - Student bookmarks a Course to resume later.
        - Student bookmarks a Resource (PDF) for quick access.
        - Student bookmarks an Exercise to retry.
        - Student bookmarks a Subject for quick navigation.
    """

    # Allowed models that can be bookmarked
    ALLOWED_MODELS = ("resource",)

    # -------------------------
    # RELATIONSHIPS
    # -------------------------
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="bookmarks",
        verbose_name=_("Student"),
        db_index=True,
    )

    content_type = models.ForeignKey(
        ContentType,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        verbose_name=_("Content Type"),
        help_text=_("Type of object being bookmarked"),
    )

    object_id = models.UUIDField(
        blank=True,
        verbose_name=_("Object ID"),
        help_text=_("ID of the object being bookmarked"),
    )

    content_object = GenericForeignKey("content_type", "object_id")

    # -------------------------
    # METADATA
    # -------------------------
    note = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Personal Note"),
        help_text=_("Optional note the student can attach to the bookmark."),
    )

    class Meta:
        verbose_name = _("Bookmark")
        verbose_name_plural = _("Bookmarks")
        ordering = ["-created_at"]
        constraints = [
            # One bookmark per student per object
            models.UniqueConstraint(
                fields=["student", "content_type", "object_id"],
                name="unique_bookmark_per_student_object",
            ),
        ]
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["student", "content_type"]),
            models.Index(fields=["student", "-created_at"]),
        ]

    # -------------------------
    # VALIDATION
    # -------------------------
    def clean(self):
        if not self.content_type or not self.object_id:
            raise ValidationError(_("Both content_type and object_id must be set."))

        if self.content_type.model not in self.ALLOWED_MODELS:
            raise ValidationError(
                _(
                    "Cannot bookmark objects of type '%(type)s'. Allowed types: %(allowed)s."
                ),
                params={
                    "type": self.content_type.model,
                    "allowed": ", ".join(self.ALLOWED_MODELS),
                },
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    # -------------------------
    # PROPERTIES
    # -------------------------
    @property
    def target_name(self) -> str:
        obj = self.content_object
        if obj is None:
            return "—"
        return getattr(obj, "title", None) or getattr(obj, "name", "—")

    @property
    def target_url(self) -> str:
        obj = self.content_object
        if obj is None:
            return "#"
        return obj.get_absolute_url() if hasattr(obj, "get_absolute_url") else "#"

    @property
    def target_type(self) -> str:
        """Returns the model name string e.g. 'course', 'resource'."""
        return self.content_type.model if self.content_type else "—"

    def get_breadcrumbs(self):
        obj = self.content_object
        return obj.get_breadcrumbs() if obj and hasattr(obj, "get_breadcrumbs") else []

    def __str__(self):
        return f"{self.student} → {self.target_type}: {self.target_name}"
