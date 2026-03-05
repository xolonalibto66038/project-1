from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _
from taggit.models import GenericUUIDTaggedItemBase, Tag, TaggedItemBase

from common.models import TimeStampModel


class UUIDTaggedItem(TimeStampModel, GenericUUIDTaggedItemBase, TaggedItemBase):
    # You need to define the tag field when using GenericUUIDTaggedItemBase
    tag = models.ForeignKey(
        Tag, related_name="uuid_tagged_items", on_delete=models.CASCADE
    )
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name=_("Content Type"),
        help_text=_("Type of object being rated"),
    )
    object_id = models.UUIDField(
        verbose_name=_("Object ID"), help_text=_("ID of the object being tagged")
    )  # 👈 Required for UUID-based PKs
    content_object = GenericForeignKey("content_type", "object_id")

    class Meta:
        verbose_name = _("05 - UUIDTag")
        verbose_name_plural = _("05 - UUIDTags")
