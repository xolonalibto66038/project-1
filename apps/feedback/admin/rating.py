from django.contrib import admin, messages
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from ..models import Rating


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):

    # ── List view ──
    list_display = (
        "student",
        "stars_display",
        "target_type",
        "object_id",
        "active_badge",
        "created_at",
    )
    list_display_links = ("student",)
    list_filter = ("active", "value", "content_type", "created_at")
    search_fields = ("student__username", "student__email", "object_id")
    # list_editable       = ('active',)
    ordering = ("-created_at",)
    list_per_page = 25
    list_max_show_all = 200

    # ── Detail view ──
    readonly_fields = (
        "content_object_display",
        "active_updated_at",
        "created_at",
        "updated_at",
        "target_type",
    )
    save_on_top = True
    preserve_filters = True
    show_full_result_count = True
    autocomplete_fields = ("student",)

    fieldsets = (
        (
            _("Who & What"),
            {
                "fields": (
                    "student",
                    "content_type",
                    "object_id",
                    "content_object_display",
                ),
                "description": _("The student and the object being rated."),
            },
        ),
        (
            _("Rating"),
            {
                "fields": ("value",),
            },
        ),
        (
            _("Status"),
            {
                "fields": ("active", "active_updated_at"),
                "description": _(
                    "Soft-delete control. Inactive ratings are excluded from averages."
                ),
            },
        ),
        (
            _("Timestamps"),
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    # ── Custom display methods ──

    @admin.display(description=_("Stars"))
    def stars_display(self, obj):
        stars = "★" * obj.value + "☆" * (5 - obj.value)
        colors = {1: "#dc3545", 2: "#fd7e14", 3: "#ffc107", 4: "#20c997", 5: "#28a745"}
        return format_html(
            '<span style="color: {}; font-size: 1.1em;">{}</span>',
            colors.get(obj.value, "#6c757d"),
            stars,
        )

    @admin.display(description=_("Status"))
    def active_badge(self, obj):
        if obj.active:
            return format_html(
                '<span style="background:#28a745; color:#fff; padding:2px 8px; border-radius:4px;">Active</span>'
            )
        return format_html(
            '<span style="background:#dc3545; color:#fff; padding:2px 8px; border-radius:4px;">Deleted</span>'
        )

    @admin.display(description=_("Target Type"))
    def target_type(self, obj):
        return obj.content_type.model if obj.content_type else "—"

    @admin.display(description=_("Object"))
    def content_object_display(self, obj):
        target = obj.content_object
        if target is None:
            return "—"
        name = getattr(target, "title", None) or getattr(target, "name", str(target))
        return format_html("<strong>{}</strong>: {}", obj.content_type.model, name)

    # ── Custom actions ──

    @admin.action(description=_("Soft-delete selected ratings"))
    def soft_delete(self, request, queryset):
        updated = queryset.filter(active=True).update(
            active=False,
            active_updated_at=timezone.now(),
        )
        self.message_user(
            request, _(f"{updated} rating(s) soft-deleted."), messages.SUCCESS
        )

    @admin.action(description=_("Restore selected ratings"))
    def restore(self, request, queryset):
        updated = queryset.filter(active=False).update(
            active=True,
            active_updated_at=timezone.now(),
        )
        self.message_user(
            request, _(f"{updated} rating(s) restored."), messages.SUCCESS
        )

    actions = ["soft_delete", "restore"]
