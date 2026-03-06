from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

from common.models import TimeStampModel

from ..choices import RatingChoice

User = get_user_model()

class Rating(TimeStampModel):
    """
    Generic rating model that allows users to rate any object in the system.

    This model uses Django's Generic Foreign Key to allow ratings on any model
    (Resources, Courses, etc.) in the Educational Management System.

    Business Rules:
    - Each student can only rate an object once (enforced by unique constraint)
    - Ratings can be soft-deleted using the 'active' field
    - Only authenticated users can create ratings
    """

    ALLOWED_MODELS = ("resource",)

    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="ratings",
        verbose_name=_("Student"),
        db_index=True,
    )

    # Rating value - using choices for validation
    value = models.PositiveSmallIntegerField(
        choices=RatingChoice.choices,
        verbose_name=_("Rating Value"),
        help_text=_("Rating value from the predefined choices"),
    )

    # Generic Foreign Key fields for polymorphic relationships
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name=_("Content Type"),
        help_text=_("Type of object being rated"),
    )

    object_id = models.UUIDField(
        verbose_name=_("Object ID"), help_text=_("ID of the object being rated")
    )

    content_object = GenericForeignKey("content_type", "object_id")

    # Soft delete functionality
    active = models.BooleanField(
        default=True,
        verbose_name=_("Active"),
        help_text=_("Whether this rating is active (soft delete)"),
    )

    # Track when the rating was activated/deactivated
    active_updated_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Active Status Updated At"),
        help_text=_("Timestamp when active status was last changed"),
    )

    class Meta:
        verbose_name = _("Rating")
        verbose_name_plural = _("Ratings")
        ordering = ["-created_at"]

        # unique_together = ("student", "content_type", "object_id")

        # Database constraints
        constraints = [
            models.UniqueConstraint(
                fields=["student", "content_type", "object_id"],
                name="unique_user_rating_per_object",
                condition=models.Q(
                    active=True
                ),  # Only enforce uniqueness for active ratings
                violation_error_message=_("Student has already rated this object."),
            ),
            models.CheckConstraint(
                check=models.Q(value__gte=1),  # Assuming ratings start from 1
                name="rating_value_positive",
                violation_error_message=_("Rating value must be positive."),
            ),
        ]

        # Database indexes for performance
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["student", "active"]),
            models.Index(fields=["active", "created_at"]),
        ]

    def __str__(self):
        """String representation of the rating."""
        rating_display = self.get_value_display() if self.value else "No rating"
        return f"{rating_display} by {self.student.username} on {self.content_object}"

    def __repr__(self):
        """Developer-friendly representation."""
        return (
            f"Rating(id={self.id}, student={self.user_id}, "
            f"value={self.value}, content_type={self.content_type_id}, "
            f"object_id={self.object_id}, active={self.active})"
        )

    def clean(self):
        """
        Model validation logic.

        Validates:
        1. The target object exists
        2. The content type allows ratings
        3. User permissions (if needed)
        """
        super().clean()

        # Validate that the target object exists
        if self.content_type and self.object_id:
            model_class = self.content_type.model_class()

            if not model_class:
                raise ValidationError({"content_type": _("Invalid content type.")})

            if self.content_type.model not in self.ALLOWED_MODELS:
                raise ValidationError(
                    f"Rating not allowed for '{self.content_type.model}'. "
                    f"Allowed: {', '.join(self.ALLOWED_MODELS)}"
                )

            if not model_class.objects.filter(pk=self.object_id).exists():
                raise ValidationError(
                    {
                        "object_id": _(
                            f"The object with ID {self.object_id} does not exist "
                            f"in {model_class.__name__}."
                        )
                    }
                )

        # Validate rating value is provided
        if self.value is None:
            raise ValidationError({"value": _("Rating value is required.")})

    def save(self, *args, **kwargs):
        """
        Override save to handle active status changes and run validation.
        """
        # Track active status changes
        if self.pk:
            try:
                old_instance = Rating.objects.get(pk=self.pk)
                if old_instance.active != self.active:
                    self.active_updated_at = timezone.now()
            except Rating.DoesNotExist:
                pass

        # Run full validation
        self.full_clean()

        super().save(*args, **kwargs)

    def soft_delete(self):
        """
        Soft delete the rating by setting active=False.
        """
        self.active = False
        self.active_updated_at = timezone.now()
        self.save(update_fields=["active", "active_updated_at"])

    def restore(self):
        """
        Restore a soft-deleted rating.
        """
        self.active = True
        self.active_updated_at = timezone.now()
        self.save(update_fields=["active", "active_updated_at"])

    @property
    def is_recent(self, days=7):
        """
        Check if rating was created recently (within specified days).
        """
        return (timezone.now() - self.created_at).days <= days

    @classmethod
    def get_average_rating(cls, content_type, object_id):
        """
        Get average rating for a specific object.

        Args:
            content_type: ContentType instance
            object_id: UUID of the object

        Returns:
            dict: {'average': float, 'count': int}
        """
        from django.db.models import Avg, Count

        result = (
            cls.objects.active()
            .filter(content_type=content_type, object_id=object_id)
            .aggregate(average=Avg("value"), count=Count("id"))
        )

        return {
            "average": round(result["average"], 2) if result["average"] else 0,
            "count": result["count"],
        }
