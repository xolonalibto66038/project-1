# apps/assessment/signals.py

from django.core.exceptions import ValidationError
from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from .models import Answer, Choice


@receiver(m2m_changed, sender=Answer.selected_choices.through)
def validate_answer_choices(sender, instance, action, **kwargs):
    """
    Fires after selected_choices M2M is modified.
    Ensures no conflict with text/boolean answers.
    """
    if action not in ('post_add', 'post_remove'):
        return

    has_choices = instance.selected_choices.exists()

    if has_choices and instance.answer_text:
        raise ValidationError(
            _('Cannot have both selected choices and a text answer.')
        )

    if has_choices and instance.answer_boolean is not None:
        raise ValidationError(
            _('Cannot have both selected choices and a boolean answer.')
        )


@receiver(post_save, sender=Choice)
def validate_mcq_after_choice_save(sender, instance, **kwargs):
    """
    Validates MCQ choice consistency every time a Choice is saved.
    Logs a warning instead of raising — raising in post_save
    would leave the DB in an inconsistent state since the
    choice is already committed.
    Use validate_choices() explicitly in forms/admin for hard enforcement.
    """
    question = instance.question
    try:
        question.validate_choices()
    except Exception as e:
        # logger.warning(
        #     f'MCQ validation warning for question {question.pk}: {e}'
        # )
        print(f"erro : {e}")


@receiver(m2m_changed, sender=Answer.selected_choices.through)
def validate_answer_choices(sender, instance, action, **kwargs):
    """
    Fires after selected_choices M2M is modified.
    Ensures no conflict with text/boolean answers.
    """
    if action not in ('post_add', 'post_remove'):
        return

    has_choices = instance.selected_choices.exists()

    if has_choices and instance.answer_text:
        raise ValidationError(
            _('Cannot have both selected choices and a text answer.')
        )

    if has_choices and instance.answer_boolean is not None:
        raise ValidationError(
            _('Cannot have both selected choices and a boolean answer.')
        )