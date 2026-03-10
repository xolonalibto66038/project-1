from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from ..models import TrueFalseQuestion
from .question import BaseQuestionAdmin


@admin.register(TrueFalseQuestion)
class TrueFalseQuestionAdmin(BaseQuestionAdmin):  # ✅ inherits BaseQuestionAdmin

    list_display = BaseQuestionAdmin.list_display + [
        "correct_answer_display",
    ]
    list_filter = BaseQuestionAdmin.list_filter + ["correct_answer"]
    ordering = ("-created_at",)

    fieldsets = (
        (
            _("Question Content"),
            {
                "fields": ("title", "question_text"),
            },
        ),
        (
            _("Answer"),
            {
                "fields": ("correct_answer", "explanation"),
                "description": _(
                    "Set the correct answer for this True/False question."
                ),
            },
        ),
        (
            _("Settings"),
            {
                "fields": ("points", "difficulty_level", "is_active"),
            },
        ),
        (
            _("Metadata"),
            {
                "fields": ("created_by", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    @admin.display(description=_("Correct Answer"))
    def correct_answer_display(self, obj):
        from django.utils.html import format_html

        if obj.correct_answer:
            return format_html(
                '<span style="color:#28a745; font-weight:bold;">✓ True</span>'
            )
        return format_html(
            '<span style="color:#dc3545; font-weight:bold;">✗ False</span>'
        )
