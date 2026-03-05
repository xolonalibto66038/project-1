from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse, path
from django.http import HttpResponseRedirect
from django.contrib import messages

from ..models import GradeSubject


@admin.register(GradeSubject)
class GradeSubjectAdmin(admin.ModelAdmin):

    list_display        = ('grade', 'subject', 'specialty', 'level_display', 'edit_button', 'delete_button')
    list_display_links  = ('grade', 'subject')
    list_filter         = ('grade__level', 'grade', 'subject', 'specialty')
    search_fields       = ('grade__name', 'subject__name', 'specialty__name')
    ordering            = ('grade__level__order', 'grade__order', 'subject__name')
    list_per_page       = 30
    list_max_show_all   = 200
    save_on_top         = True
    preserve_filters    = True
    show_full_result_count = True
    autocomplete_fields = ('grade', 'subject', 'specialty')

    fieldsets = (
        (_('Assignment'), {
            'fields': ('grade', 'subject', 'specialty'),
            'description': _(
                'Assign a subject to a grade. '
                'Leave specialty blank if the subject applies to all specialties of this grade.'
            ),
        }),
    )

    # ── Custom display methods ──

    @admin.display(description=_('Level'))
    def level_display(self, obj):
        return obj.grade.level.get_name_display()

    # ── Custom actions ──

    @admin.action(description=_('Duplicate selected assignments'))
    def duplicate_assignments(self, request, queryset):
        duplicated = 0
        for obj in queryset:
            obj.pk = None
            try:
                obj.save()
                duplicated += 1
            except Exception:
                pass
        self.message_user(
            request,
            _(f'{duplicated} assignment(s) duplicated successfully.'),
            messages.SUCCESS,
        )

    actions = ['duplicate_assignments']

    def edit_button(self, obj: GradeSubject) -> str:
        """Render an Edit button linking to the change page for the object."""
        url = reverse(
            "admin:%s_%s_change" % (obj._meta.app_label, obj._meta.model_name),
            args=[obj.pk],
        )
        return format_html(
            '<a class="button" href="{}" style="padding: 5px 10px; background-color: #417690; color: white; text-decoration: none; border-radius: 3px;">{}</a>',
            url,
            _("Edit"),
        )

    edit_button.short_description = _("Edit")
    edit_button.allow_tags = True

    def delete_button(self, obj: GradeSubject) -> str:
        """Render a Delete button linking to the delete page for the object."""
        url = reverse(
            "admin:%s_%s_delete" % (obj._meta.app_label, obj._meta.model_name),
            args=[obj.pk],
        )
        return format_html(
            '<a class="button" href="{}" style="padding: 5px 10px; background-color: #dc3545; color: white; text-decoration: none; border-radius: 3px;">{}</a>',
            url,
            _("Delete"),
        )

    delete_button.short_description = _("Delete")
    delete_button.allow_tags = True


class GradeSubjectInline(admin.TabularInline):
    model = GradeSubject
    extra = 0
    fields = ('subject', 'specialty')
    autocomplete_fields = ('subject', 'specialty')