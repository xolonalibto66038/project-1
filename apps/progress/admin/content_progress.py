# apps/progress/admin/content_progress_admin.py

from django.contrib import admin, messages
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from ..models import ContentProgress


@admin.register(ContentProgress)
class ContentProgressAdmin(admin.ModelAdmin):

    # ── List view ──
    list_display = (
        "student",
        "target_type",
        "object_id",
        "status_badge",
        "first_viewed_at",
        "completed_at",
    )
    list_display_links = ("student",)
    list_filter = (
        "is_completed",
        "content_type",
        "created_at",
        "completed_at",
    )
    search_fields = (
        "student__username",
        "student__email",
        "object_id",
    )
    ordering = ("-created_at",)
    list_per_page = 25
    list_max_show_all = 200

    # ── Detail view ──
    readonly_fields = (
        "content_object_display",
        "target_type",
        "first_viewed_at",
        "completed_at",
        "created_at",
        "updated_at",
    )
    save_on_top = True
    preserve_filters = True
    show_full_result_count = True
    autocomplete_fields = ("student",)

    fieldsets = (
        (
            _("Student"),
            {
                "fields": ("student",),
            },
        ),
        (
            _("Target"),
            {
                "fields": (
                    "content_type",
                    "object_id",
                    "content_object_display",
                    "target_type",
                ),
                "description": _("The course or resource being tracked."),
            },
        ),
        (
            _("Progress"),
            {
                "fields": ("is_completed",),
                "description": _(
                    "Use the actions below to mark complete/incomplete safely. "
                    "Editing is_completed directly bypasses race-condition protection."
                ),
            },
        ),
        (
            _("Timestamps"),
            {
                "fields": (
                    "first_viewed_at",
                    "completed_at",
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    # ── Prevent direct edits to progress fields ──
    # Completions should go through mark_completed() / mark_incomplete()
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    # ── Custom display methods ──

    @admin.display(description=_("Type"))
    def target_type(self, obj):
        if not obj.content_type:
            return "—"
        colors = {
            "course": "#007bff",
            "resource": "#28a745",
        }
        color = colors.get(obj.content_type.model, "#6c757d")
        return format_html(
            '<span style="background:{}; color:#fff; padding:2px 8px; '
            'border-radius:4px; font-size:0.85em;">{}</span>',
            color,
            obj.content_type.model.capitalize(),
        )

    @admin.display(description=_("Status"))
    def status_badge(self, obj):
        if obj.is_completed:
            return format_html(
                '<span style="background:#28a745; color:#fff; padding:2px 8px; '
                'border-radius:4px;">✓ Completed</span>'
            )
        return format_html(
            '<span style="background:#ffc107; color:#000; padding:2px 8px; '
            'border-radius:4px;">⏳ In Progress</span>'
        )

    @admin.display(description=_("Object"))
    def content_object_display(self, obj):
        target = obj.content_object
        if target is None:
            return format_html(
                '<span style="color:#dc3545;">Object no longer exists</span>'
            )
        name = getattr(target, "title", None) or getattr(target, "name", str(target))
        return format_html(
            "<strong>{}</strong>: {}",
            obj.content_type.model,
            name,
        )

    # ── Custom actions ──

    @admin.action(description=_("Mark selected as Completed"))
    def mark_completed(self, request, queryset):
        success = 0
        skipped = 0
        for obj in queryset.filter(is_completed=False):
            if obj.mark_completed():
                success += 1
            else:
                skipped += 1
        if success:
            self.message_user(
                request,
                _(f"{success} record(s) marked as completed."),
                messages.SUCCESS,
            )
        if skipped:
            self.message_user(
                request,
                _(
                    f"{skipped} record(s) skipped (already completed or race condition)."
                ),
                messages.WARNING,
            )

    @admin.action(description=_("Mark selected as Incomplete"))
    def mark_incomplete(self, request, queryset):
        success = 0
        skipped = 0
        for obj in queryset.filter(is_completed=True):
            if obj.mark_incomplete():
                success += 1
            else:
                skipped += 1
        if success:
            self.message_user(
                request,
                _(f"{success} record(s) marked as incomplete."),
                messages.SUCCESS,
            )
        if skipped:
            self.message_user(
                request,
                _(
                    f"{skipped} record(s) skipped (already incomplete or race condition)."
                ),
                messages.WARNING,
            )

    @admin.action(description=_("Delete selected progress records permanently"))
    def hard_delete(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(
            request,
            _(f"{count} progress record(s) permanently deleted."),
            messages.WARNING,
        )

    actions = ["mark_completed", "mark_incomplete", "hard_delete"]
