from django.db import models
from django.utils.translation import gettext_lazy as _


class PlanInterval(models.TextChoices):
    MONTHLY    = 'month',  _('1 Month')
    BIANNUAL   = '6month', _('6 Months')
    ANNUAL     = 'year',   _('12 Months')


class OfferTier(models.TextChoices):
    FREE     = 'free',     _('Free')
    STANDARD = 'standard', _('Standard')
    PREMIUM  = 'premium',  _('Premium')
