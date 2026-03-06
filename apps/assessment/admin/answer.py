# apps/assessment/admin/answer_admin.py

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.utils import timezone

from ..models import Answer


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):

    list_display        = (
        'student', 'question_type_display', 'answer_preview_display',
        'correctness_badge', 'points_earned', 'is_graded_display',
        'submitted_at',
    )
    list_display_links  = ('student',)
    list_filter         = (
        'question_content_type',
        'is_correct',
        'answer_boolean',
        'submitted_at',
    )
    search_fields       = (
        'student__email',
        'student__first_name',
        'student__last_name',
        'answer_text',
        'feedback',
    )
    ordering            = ('-submitted_at',)
    list_per_page       = 25
    list_max_show_all   = 200
    save_on_top         = True
    preserve_filters    = True
    show_full_result_count = True
    autocomplete_fields = ('student',)

    readonly_fields = (
        'submitted_at', 'graded_at',
        'created_at',   'updated_at',
        'answer_preview_display',
    )

    fieldsets = (
        (_('Who & What'), {
            'fields': ('student', 'attempt', 'question_content_type', 'question_object_id'),
        }),
        (_('Answer'), {
            'fields': ('answer_text', 'answer_boolean', 'selected_choices'),
            'description': _('Only one answer type should be filled.'),
        }),
        (_('Grading'), {
            'fields': ('is_correct', 'points_earned', 'feedback', 'graded_by', 'graded_at'),
        }),
        (_('Timestamps'), {
            'fields': ('submitted_at', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    # ── Custom display methods ──

    @admin.display(description=_('Question Type'))
    def question_type_display(self, obj):
        return obj.content_type.model.replace('question', '').title() \
            if obj.question_content_type else '—'

    @admin.display(description=_('Answer'))
    def answer_preview_display(self, obj):
        return obj.answer_preview

    @admin.display(description=_('Correct'))
    def correctness_badge(self, obj):
        if obj.is_correct is None:
            return format_html(
                '<span style="background:#ffc107; color:#000; padding:2px 8px; border-radius:4px;">⏳ Pending</span>'
            )
        if obj.is_correct:
            return format_html(
                '<span style="background:#28a745; color:#fff; padding:2px 8px; border-radius:4px;">✓ Correct</span>'
            )
        return format_html(
            '<span style="background:#dc3545; color:#fff; padding:2px 8px; border-radius:4px;">✗ Wrong</span>'
        )

    @admin.display(description=_('Graded'), boolean=True)
    def is_graded_display(self, obj):
        return obj.is_graded

    # ── Actions ──

    @admin.action(description=_('Mark selected answers as correct'))
    def mark_correct(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(
            is_correct=True,
            graded_at=timezone.now(),
            graded_by=request.user,
        )
        self.message_user(request, _(f'{updated} answer(s) marked correct.'))

    @admin.action(description=_('Mark selected answers as incorrect'))
    def mark_incorrect(self, request, queryset):
        updated = queryset.update(
            is_correct=False,
            points_earned=0,
            graded_at=timezone.now(),
            graded_by=request.user,
        )
        self.message_user(request, _(f'{updated} answer(s) marked incorrect.'))

    actions = ['mark_correct', 'mark_incorrect']

# from django.contrib import admin
# from django.urls import reverse
# from django.utils.html import format_html
# from django.utils.translation import gettext_lazy as _

# from ..models import Answer


# class AnswerAdmin(admin.ModelAdmin):
#     list_display = [
#         "question_content_type",
#         "question_object_id",
#         "points_earned",
#         "is_correct",
#         "user_full_name",
#         "edit_button",
#         "delete_button",
#     ]
#     autocomplete_fields = ("student",)
#     list_filter = ["question_content_type", "answer_boolean"]
#     search_fields = ["answer_text", "feedback", "student__user__username"]
#     readonly_fields = [
#         "id",
#         "created_at",
#         "updated_at",
#         "submitted_at",
#         "graded_at",
#         "question",
#     ]

#     # Pagination
#     list_per_page = 15
#     list_max_show_all = 100

#     # Advanced features
#     save_on_top = True
#     preserve_filters = True

#     # Custom methods to display in list view
#     def user_full_name(self, obj) -> str:
#         """Display the full name of the associated user."""
#         return obj.student.get_full_name()

#     user_full_name.short_description = _("Full Name")

#     def edit_button(self, obj):
#         """Render an Edit button linking to the change page for the object."""
#         url = reverse(
#             "admin:%s_%s_change" % (obj._meta.app_label, obj._meta.model_name),
#             args=[obj.pk],
#         )
#         return format_html(
#             '<a class="button" href="{}" style="padding: 5px 10px; background-color: #417690; color: white; text-decoration: none; border-radius: 3px;">{}</a>',
#             url,
#             _("Edit"),
#         )

#     edit_button.short_description = _("Edit")
#     edit_button.allow_tags = True  # Allow HTML in the column

#     def delete_button(self, obj):
#         """Render a Delete button linking to the delete page for the object."""
#         url = reverse(
#             "admin:%s_%s_delete" % (obj._meta.app_label, obj._meta.model_name),
#             args=[obj.pk],
#         )
#         return format_html(
#             '<a class="button" href="{}" style="padding: 5px 10px; background-color: #dc3545; color: white; text-decoration: none; border-radius: 3px;">{}</a>',
#             url,
#             _("Delete"),
#         )

#     delete_button.short_description = _("Delete")
#     delete_button.allow_tags = True  # Allow HTML in the column

#     # Actions for bulk operations
#     actions = (
#         "mark_as_active",
#         "mark_as_inactive",
#     )

#     def mark_as_active(self, request, queryset):
#         """Action to mark selected Grades as active."""
#         updated = queryset.update(is_active=True)
#         self.message_user(
#             request,
#             _(f"Successfully marked {updated} Grade(s) as active."),
#         )

#     mark_as_active.short_description = _("Mark selected Grades as active")

#     def mark_as_inactive(self, request, queryset):
#         """Action to mark selected Grades as inactive."""
#         updated = queryset.update(is_active=False)
#         self.message_user(
#             request,
#             _(f"Successfully marked {updated} Grade(s) as inactive."),
#         )

#     mark_as_inactive.short_description = _("Mark selected Grades as inactive")


# admin.site.register(Answer, AnswerAdmin)
