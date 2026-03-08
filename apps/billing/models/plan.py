from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from common.models import TimeStampModel
from ..choices import PlanInterval

User = get_user_model()

class Plan(TimeStampModel):
    """
    A purchasable plan: Offer × Interval × Price.
    Free offer has no plans.
    """
    offer            = models.ForeignKey(
        "Offer",
        on_delete=models.CASCADE,
        related_name='plans',
    )
    interval         = models.CharField(
        max_length=10,
        choices=PlanInterval.choices,
    )
    stripe_price_id  = models.CharField(
        max_length=100,
        unique=True,
        null=True,        # ← allow NULL (not empty string)
        blank=True,
        default=None,     # ← default to NULL not ''
        help_text=_('Set this after creating the price in Stripe dashboard.')
    )
    price            = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        help_text=_('Price in EUR for this interval.')
    )
    original_price   = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Original price before discount — shown as strikethrough.')
    )
    is_active        = models.BooleanField(default=True)
    is_popular       = models.BooleanField(
        default=False,
        help_text=_('Highlights this plan with a "Most Popular" badge.')
    )

    class Meta:
        unique_together = ('offer', 'interval')
        ordering        = ['offer__order', 'interval']

    def __str__(self):
        return f"{self.offer.name} — {self.get_interval_display()}"

    @property
    def savings_percent(self):
        if self.original_price and self.original_price > self.price:
            saving = (self.original_price - self.price) / self.original_price * 100
            return round(saving)
        return None

    @property
    def price_per_month(self):
        divisor = {'month': 1, '6month': 6, 'year': 12}.get(self.interval, 1)
        return round(self.price / divisor, 2)