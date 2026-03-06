from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse, path
from django.http import HttpResponseRedirect
from django.contrib import messages

from ..models import Course, Chapter
from .resource import ResourceInline
from .video import VideoResourceInline

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):

    # ── List view ──
    list_display        = ('title', 'parent_display', 'effective_term', 'difficulty', 'is_active', 'resource_count', 'video_count', 'slug')
    list_display_links  = ('title',)
    list_filter         = ('difficulty', 'is_active', 'term', 'chapter__grade_subject__grade__level', 'chapter__grade_subject__grade')
    search_fields       = ('title', 'slug', 'chapter__title', 'grade_subject__subject__name')
    list_editable       = ('difficulty', 'is_active')
    ordering            = ('chapter__grade_subject__grade__level__order', 'chapter__order', 'order')
    list_per_page       = 20
    list_max_show_all   = 100

    # ── Detail view ──
    readonly_fields     = ('slug', 'effective_term', 'effective_grade_subject')
    save_on_top         = True
    preserve_filters    = True
    show_full_result_count = True
    autocomplete_fields = ('chapter', 'grade_subject')

    inlines = [ResourceInline, VideoResourceInline]

    fieldsets = (
        (_('Parent'), {
            'fields': ('chapter', 'grade_subject'),
            'description': _(
                'Assign to a chapter (standard) OR directly to a grade subject (standalone). '
                'Never both.'
            ),
        }),
        (_('Content'), {
            'fields': ('title', 'slug', 'description'),
        }),
        (_('Settings'), {
            'fields': ('order', 'term', 'difficulty', 'is_active'),
            'description': _('Term is only required for standalone courses.'),
        }),
        (_('Computed'), {
            'fields': ('effective_term', 'effective_grade_subject'),
            'classes': ('collapse',),
            'description': _('Read-only computed values for reference.'),
        }),
    )

    # ── Custom display methods ──

    @admin.display(description=_('Parent'))
    def parent_display(self, obj):
        if obj.chapter:
            url = reverse('admin:content_chapter_change', args=[obj.chapter.pk])
            return format_html('<a href="{}">📂 {}</a>', url, obj.chapter.title)
        if obj.grade_subject:
            return format_html('📚 {} (standalone)', obj.grade_subject)
        return '—'

    @admin.display(description=_('Resources'))
    def resource_count(self, obj):
        count = obj.resources.count()
        url = reverse('admin:content_resource_changelist') + f'?course__id__exact={obj.pk}'
        return format_html('<a href="{}">{} resource(s)</a>', url, count)

    @admin.display(description=_('Videos'))
    def video_count(self, obj):
        count = obj.videos.count()
        url = reverse('admin:content_videoresource_changelist') + f'?course__id__exact={obj.pk}'
        return format_html('<a href="{}">{} video(s)</a>', url, count)

    # ── Custom actions ──

    @admin.action(description=_('Activate selected courses'))
    def activate(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, _(f'{updated} course(s) activated.'), messages.SUCCESS)

    @admin.action(description=_('Deactivate selected courses'))
    def deactivate(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, _(f'{updated} course(s) deactivated.'), messages.SUCCESS)

    @admin.action(description=_('Reset slugs for selected courses'))
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
                name='content_course_duplicate',
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
            self.message_user(request, _('Course duplicated successfully.'), messages.SUCCESS)
        return HttpResponseRedirect(reverse('admin:content_course_changelist'))


class CourseInline(admin.TabularInline):
    model = Chapter.courses.field.model  # avoids circular import
    extra = 0
    fields = ('title', 'order', 'term', 'difficulty', 'is_active', 'slug')
    readonly_fields = ('slug',)
    ordering = ('order',)
    show_change_link = True
