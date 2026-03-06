from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse, path
from django.http import HttpResponseRedirect
from django.contrib import messages

from ..models.chapter import Chapter


@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):

    # ── List view ──
    list_display        = ('title', 'grade_subject', 'level_display', 'term', 'order', 'is_active', 'course_count', 'slug')
    list_display_links  = ('title',)
    list_filter         = ('term', 'is_active', 'grade_subject__grade__level', 'grade_subject__grade', 'grade_subject__subject')
    search_fields       = ('title', 'slug', 'grade_subject__subject__name', 'grade_subject__grade__name')
    list_editable       = ('order', 'is_active')
    ordering            = ('grade_subject__grade__level__order', 'grade_subject__grade__order', 'order')
    list_per_page       = 20
    list_max_show_all   = 100

    # ── Detail view ──
    readonly_fields     = ('slug',)
    save_on_top         = True
    preserve_filters    = True
    show_full_result_count = True
    autocomplete_fields = ('grade_subject',)

    fieldsets = (
        (_('Location'), {
            'fields': ('grade_subject', 'term', 'order'),
            'description': _('Where this chapter sits in the curriculum hierarchy.'),
        }),
        (_('Content'), {
            'fields': ('title', 'slug', 'description'),
        }),
        (_('Visibility'), {
            'fields': ('is_active',),
        }),
    )

    # ── Custom display methods ──

    @admin.display(description=_('Level'))
    def level_display(self, obj):
        return obj.grade_subject.grade.level.get_name_display()

    @admin.display(description=_('Courses'), ordering='courses__count')
    def course_count(self, obj):
        count = obj.courses.count()
        url = (
            reverse('admin:content_course_changelist')
            + f'?chapter__id__exact={obj.pk}'
        )
        return format_html('<a href="{}">{} course(s)</a>', url, count)

    # ── Custom actions ──

    @admin.action(description=_('Activate selected chapters'))
    def activate(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, _(f'{updated} chapter(s) activated.'), messages.SUCCESS)

    @admin.action(description=_('Deactivate selected chapters'))
    def deactivate(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, _(f'{updated} chapter(s) deactivated.'), messages.SUCCESS)

    @admin.action(description=_('Reset slugs for selected chapters'))
    def reset_slugs(self, request, queryset):
        for obj in queryset:
            obj.slug = ''
            obj.save()
        self.message_user(request, _('Slugs reset and regenerated.'), messages.SUCCESS)

    actions = ['activate', 'deactivate', 'reset_slugs']

    # ── Custom URLs ──

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                '<int:pk>/duplicate/',
                self.admin_site.admin_view(self.duplicate_view),
                name='content_chapter_duplicate',
            ),
        ]
        return custom + urls

    def duplicate_view(self, request, pk):
        obj = self.get_object(request, pk)
        if obj:
            obj.pk   = None
            obj.slug = ''
            obj.title = f"{obj.title} (copy)"
            obj.save()
            self.message_user(request, _('Chapter duplicated successfully.'), messages.SUCCESS)
        return HttpResponseRedirect(reverse('admin:content_chapter_changelist'))