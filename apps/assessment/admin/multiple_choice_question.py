from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.contrib import messages

from ..models import Choice, MultipleChoiceQuestion
from .question import BaseQuestionAdmin


# ==============================
# Choice Inline (for MCQ)
# ============================== 
class ChoiceInline(admin.TabularInline):
    model          = Choice
    extra          = 3
    fields         = ('text', 'is_correct', 'order')
    ordering       = ('order',)
    show_change_link = False

    def get_extra(self, request, obj=None, **kwargs):
        # No extra rows when editing existing question
        return 0 if obj else 3


# ==============================
# Multiple Choice Admin
# ==============================
@admin.register(MultipleChoiceQuestion)
class MultipleChoiceQuestionAdmin(BaseQuestionAdmin):
    list_display = BaseQuestionAdmin.list_display + [
        'allow_multiple', 'choice_count',
    ]
    list_filter  = BaseQuestionAdmin.list_filter + ['allow_multiple']
    ordering     = ('-created_at',)
    inlines      = [ChoiceInline]

    fieldsets = (
        (_('Question Content'), {
            'fields': ('title', 'question_text'),
        }),
        (_('MCQ Settings'), {
            'fields': ('allow_multiple', 'explanation'),
            'description': _(
                'Enable "Allow Multiple" if more than one choice can be correct.'
            ),
        }),
        (_('Settings'), {
            'fields': ('points', 'difficulty_level', 'is_active'),
        }),
        (_('Metadata'), {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description=_('Choices'))
    def choice_count(self, obj):
        total   = obj.choices.count()
        correct = obj.choices.filter(is_correct=True).count()
        return f'{total} total / {correct} correct'

    def save_related(self, request, form, formsets, change):
        """Validate MCQ choices after all inlines are saved."""
        super().save_related(request, form, formsets, change)
        try:
            form.instance.validate_choices()
        except Exception as e:
            messages.warning(request, f'Choice validation: {e}')


@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display        = ('text', 'question', 'is_correct', 'order')
    list_display_links  = ('text',)
    list_filter         = ('is_correct',)
    search_fields       = ('text', 'question__title')
    list_editable       = ('is_correct', 'order')
    ordering            = ('question', 'order')
    autocomplete_fields = ('question',)
    list_per_page       = 25
    save_on_top         = True
    preserve_filters    = True
