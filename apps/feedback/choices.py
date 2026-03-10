from django.db import models
from django.utils.translation import gettext_lazy as _


class RatingChoice(models.IntegerChoices):
    ONE = 1, _("★☆☆☆☆")
    TWO = 2, _("★★☆☆☆")
    THREE = 3, _("★★★☆☆")
    FOUR = 4, _("★★★★☆")
    FIVE = 5, _("★★★★★")
    __empty__ = _("Rate this")


class InteractionType(models.TextChoices):
    VIEW = "view", _("View")
    DOWNLOAD = "download", _("Download")
    RATE = "rate", _("Rate")
    BOOKMARK = "bookmark", _("Bookmark")
