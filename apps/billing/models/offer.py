from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from common.models import TimeStampModel
from ..choices import OfferTier

User = get_user_model()


class Offer(TimeStampModel):
    """
    The three tiers: Free / Standard / Premium.
    Describes features — not prices.
    """
    tier        = models.CharField(
        max_length=20,
        choices=OfferTier.choices,
        unique=True,
    )
    name        = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    features    = models.JSONField(
        default=list,
        help_text=_('List of feature strings shown on pricing page.')
    )
    is_active   = models.BooleanField(default=True)
    order       = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name

    @property
    def is_free(self):
        return self.tier == OfferTier.FREE
