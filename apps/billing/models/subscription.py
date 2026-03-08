from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from common.models import TimeStampModel

User = get_user_model()


class Subscription(TimeStampModel):
    """
    Active subscription for a user.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='subscription',
    )
    plan = models.ForeignKey(
        "Plan",
        on_delete=models.PROTECT,
        related_name='subscriptions',
    )
    stripe_subscription_id = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
    )
    stripe_customer_id     = models.CharField(
        max_length=100,
        blank=True,
    )
    status                 = models.CharField(
        max_length=20,
        choices=[
            ('active',    'Active'),
            ('trialing',  'Trialing'),
            ('past_due',  'Past Due'),
            ('canceled',  'Canceled'),
            ('incomplete','Incomplete'),
        ],
        default='active',
    )
    current_period_end     = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end   = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('Subscription')

    def __str__(self):
        return f"{self.user} — {self.plan} ({self.status})"

    @property
    def is_active(self):
        return self.status in ('active', 'trialing')

    @property
    def tier(self):
        return self.plan.offer.tier