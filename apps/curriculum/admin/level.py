from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse, path
from django.http import HttpResponseRedirect
from django.contrib import messages

from ..models import Level
from .grade import GradeInline


@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):

    # ── List view ──
    list_display        = ('colored_name', 'slug', 'order', 'grade_count', 'subject_count', 'edit_button', 'delete_button')
    list_display_links  = ('colored_name',)
    list_filter         = ('name',)
    search_fields       = ('name', 'slug')
    list_editable       = ('order',)
    ordering            = ('order',)
    list_per_page       = 10
    list_max_show_all   = 50

    # ── Detail view ──
    readonly_fields     = ('slug',)
    save_on_top         = True
    preserve_filters    = True
    show_full_result_count = True

    inlines = [GradeInline]

    fieldsets = (
        (_('General Information'), {
            'fields': ('name', 'slug', 'order'),
            'description': _('Basic information about the education level.'),
        }),
    )

    # ── Custom display methods ──

    @admin.display(description=_('Name'))
    def colored_name(self, obj):
        colors = {
            'primaire':   '#28a745',
            'moyen':      '#007bff',
            'secondaire': '#dc3545',
        }
        color = colors.get(obj.name, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_name_display(),
        )

    @admin.display(description=_('Grades'))
    def grade_count(self, obj):
        count = obj.grades.count()
        url = (
            reverse('admin:curriculum_grade_changelist')
            + f'?level__id__exact={obj.pk}'
        )
        return format_html('<a href="{}">{} grade(s)</a>', url, count)

    @admin.display(description=_('Subjects'))
    def subject_count(self, obj):
        count = obj.subjects.count()
        url = (
            reverse('admin:curriculum_subject_changelist')
            + f'?level__id__exact={obj.pk}'
        )
        return format_html('<a href="{}">{} subject(s)</a>', url, count)

    def edit_button(self, obj: Level) -> str:
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

    def delete_button(self, obj: Level) -> str:
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

    # ── Custom actions ──

    @admin.action(description=_('Reset slugs for selected levels'))
    def reset_slugs(self, request, queryset):
        for obj in queryset:
            obj.slug = ''
            obj.save()
        self.message_user(request, _('Slugs have been reset and regenerated.'), messages.SUCCESS)

    actions = ['reset_slugs']

    # ── Custom URLs ──

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                '<int:pk>/duplicate/',
                self.admin_site.admin_view(self.duplicate_view),
                name='curriculum_level_duplicate',
            ),
        ]
        return custom + urls

    def duplicate_view(self, request, pk):
        obj = self.get_object(request, pk)
        if obj:
            obj.pk   = None
            obj.slug = ''
            obj.name = f"{obj.name}_copy"
            obj.save()
            self.message_user(request, _('Level duplicated successfully.'), messages.SUCCESS)
        return HttpResponseRedirect(reverse('admin:curriculum_level_changelist'))