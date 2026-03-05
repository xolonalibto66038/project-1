from django.db import models
from django.utils.translation import gettext_lazy as _


class LevelChoices(models.TextChoices):
    PRIMAIRE    = 'primaire',    _('Primaire')
    MOYEN       = 'moyen',       _('Moyen')
    SECONDAIRE  = 'secondaire',  _('Secondaire')
    UNIVERSITY  = 'university',  _('University')
