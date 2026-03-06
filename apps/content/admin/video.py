# apps/content/admin/video_resource_admin.py

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse, path
from django.http import HttpResponseRedirect
from django.contrib import messages

from ..models import Course, VideoResource


@admin.register(VideoResource)
class VideoResourceAdmin(admin.ModelAdmin):

    # ── List view ──
    list_display        = ('title', 'course', 'order', 'duration', 'is_active', 'youtube_preview', 'created_at')
    list_display_links  = ('title',)
    list_filter         = (
        'is_active',
        'course__chapter__grade_subject__grade__level',
        'course__chapter__grade_subject__subject',
    )
    search_fields       = ('title', 'youtube_url', 'course__title')
    list_editable       = ('order', 'is_active')
    ordering            = ('course', 'order')
    list_per_page       = 25
    list_max_show_all   = 200

    # ── Detail view ──
    readonly_fields     = ('youtube_preview', 'youtube_id_display', 'created_at', 'updated_at')
    save_on_top         = True
    preserve_filters    = True
    show_full_result_count = True
    autocomplete_fields = ('course',)

    fieldsets = (
        (_('Course'), {
            'fields': ('course',),
        }),
        (_('Video'), {
            'fields': ('title', 'youtube_url', 'youtube_id_display', 'duration', 'order'),
            'description': _('Paste the full YouTube URL. The video ID is extracted automatically.'),
        }),
        (_('Visibility'), {
            'fields': ('is_active',),
        }),
        (_('Tags'), {
            'fields': ('tags',),
            'classes': ('collapse',),
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    # ── Custom display methods ──

    @admin.display(description=_('Preview'))
    def youtube_preview(self, obj):
        vid = obj.youtube_id
        if vid:
            thumb = f"https://img.youtube.com/vi/{vid}/mqdefault.jpg"
            link  = f"https://www.youtube.com/watch?v={vid}"
            return format_html(
                '<a href="{}" target="_blank">'
                '<img src="{}" style="height:60px; border-radius:4px;"/>'
                '</a>',
                link, thumb,
            )
        return '—'

    @admin.display(description=_('YouTube ID'))
    def youtube_id_display(self, obj):
        vid = obj.youtube_id
        if vid:
            return format_html(
                '<code>{}</code> '
                '<a href="https://www.youtube.com/watch?v={}" target="_blank">▶ Watch</a>',
                vid, vid,
            )
        return '—'

    # ── Custom actions ──

    @admin.action(description=_('Activate selected videos'))
    def activate(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, _(f'{updated} video(s) activated.'), messages.SUCCESS)

    @admin.action(description=_('Deactivate selected videos'))
    def deactivate(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, _(f'{updated} video(s) deactivated.'), messages.SUCCESS)

    actions = ['activate', 'deactivate']

    # ── Custom URLs ──

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                '<int:pk>/duplicate/',
                self.admin_site.admin_view(self.duplicate_view),
                name='content_videoresource_duplicate',
            ),
        ]
        return custom + urls

    def duplicate_view(self, request, pk):
        obj = self.get_object(request, pk)
        if obj:
            obj.pk    = None
            obj.title = f"{obj.title} (copy)"
            obj.save()
            self.message_user(request, _('Video duplicated successfully.'), messages.SUCCESS)
        return HttpResponseRedirect(reverse('admin:content_videoresource_changelist'))


class VideoResourceInline(admin.TabularInline):
    model = Course.videos.field.model
    extra = 0
    fields = ('title', 'youtube_url', 'order', 'is_active')
    ordering = ('order',)
    show_change_link = True