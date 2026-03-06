from django.db import models
from django.utils.translation import gettext_lazy as _


class QuestionType(models.TextChoices):
    ESSAY = "essay", _("Essay")
    MCQ = "mcq", _("Multiple Choice")
    TF = "tf", _("True / False")
